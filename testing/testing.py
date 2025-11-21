import abc
import io
import os
import subprocess
import typing

test_groups: dict[int, tuple[str, str]] = {}
for filename in os.listdir('tests'):
    test_num, _, test_name = filename.partition(' - ')
    test_num = int(test_num)
    test_name = test_name.removesuffix('.mdstest')
    test_groups[test_num] = (filename, test_name)

print(test_groups)

ANSI_WHITE = '\33[0m'
ANSI_FAILURE = '\33[91m'
ANSI_SUCCESS = '\33[32m'


class TestReport(abc.ABC):
    @abc.abstractmethod
    def to_short_string(self) -> str:
        pass

    @abc.abstractmethod
    def to_detailed_string(self) -> str:
        pass


class TestReportFailed(TestReport):
    def __init__(self, test_name: str, failed_condition: str, failure_value: bytes, expected_value: bytes, stdout: bytes, stderr: bytes):
        if type(test_name) is not str:
            raise ValueError()
        self.test_name = test_name
        self.failed_condition = failed_condition
        self.failure_value = failure_value
        self.expected_value = expected_value
        self.stdout = stdout
        self.stderr = stderr

    def to_short_string(self) -> str:
        return f'{ANSI_FAILURE} X {ANSI_WHITE}'

    def _escape_bytes(self, key: str, s: bytes, allow_ansi_escape: bool = True) -> str:
        out = io.StringIO()
        out.write(f'### {key}:\n')
        for c in s:
            if c == '\\':
                out.write('\\\\')
            elif 31 < c < 127 or c in b'\n ':
                out.write(chr(c))
            elif c == 27 and allow_ansi_escape:
                out.write(chr(c))
            else:
                out.write(f'\\x{c:02x}')
        out.write('\n###')
        return out.getvalue()

    def to_detailed_string(self) -> str:
        out = io.StringIO()

        out.write(f'### test_name: {self.test_name!r}\n')
        out.write(f'### failed_condition: {self.failed_condition!r}\n')

        out.write(self._escape_bytes('failure_value', self.failure_value) + '\n')
        out.write(self._escape_bytes('expected_value', self.expected_value) + '\n')

        out.write(self._escape_bytes('stdout', self.stdout) + '\n')
        out.write(self._escape_bytes('stderr', self.stderr))

        return out.getvalue()


class TestReportSucceeded(TestReport):
    def __init__(self, test_name: str):
        self.test_name = test_name

    def to_short_string(self) -> str:
        return f'{ANSI_SUCCESS} . {ANSI_WHITE}'

    def to_detailed_string(self) -> str:
        return f'Test succeeded: {self.test_name!r}\n'


class Test:
    def __init__(self, name: str, program_source: bytes, program_stdout: bytes = b'', program_stderr: bytes = b'', compiler_stderr: bytes | None = None, compiler_return_code: int = 0, run_program: bool = True):
        if type(name) is not str:
            raise ValueError()
        self.name = name
        self.program_source = program_source
        if type(program_stdout) is not bytes:
            raise ValueError()
        self.program_stdout = program_stdout
        if type(program_stderr) is not bytes:
            raise ValueError()
        self.program_stderr = program_stderr
        self.compiler_stderr = compiler_stderr
        if type(compiler_return_code) is not int:
            raise ValueError()
        self.compiler_return_code = compiler_return_code
        if type(run_program) is not bool:
            raise ValueError()
        self.run_program = run_program

    def run(self) -> TestReport:
        compiler_result = subprocess.run(
            ['python3', '../main.py', '-o', './test', '-'],
            capture_output=True,
            input=self.program_source)

        if compiler_result.returncode != self.compiler_return_code:
            return TestReportFailed(self.name, 'compiler_return_code', str(compiler_result.returncode).encode(), str(self.compiler_return_code).encode(), compiler_result.stdout, compiler_result.stderr)
        if self.compiler_stderr is not None and compiler_result.stderr != self.compiler_stderr:
            return TestReportFailed(self.name, 'compiler_stderr', compiler_result.stderr, self.compiler_stderr, compiler_result.stdout, compiler_result.stderr)

        if self.run_program:
            program_result = subprocess.run(
                ['./test'],
                capture_output=True
            )

            if program_result.stderr != self.program_stderr:
                return TestReportFailed(self.name, 'program_stderr', program_result.stderr, self.program_stderr, compiler_result.stdout, compiler_result.stderr)
            if program_result.stdout != self.program_stdout:
                return TestReportFailed(self.name, 'program_stdout', program_result.stdout, self.program_stdout, compiler_result.stdout, compiler_result.stderr)

        return TestReportSucceeded(self.name)

    def __repr__(self):
        return '<Test ' + ', '.join(f'self.{k}={getattr(self, k)}' for k in self.__dict__) + '>'


def parse_tests(file: typing.TextIO) -> list[Test]:
    def peek() -> str:
        pos = file.tell()
        c = file.read(1)
        file.seek(pos)
        return c

    def accept(s: str):
        if s != (v := file.read(len(s))):
            raise SyntaxError(f'Expected {s!r} but got {v!r}')

    def parse_string() -> bytes:
        out = io.BytesIO()
        while c := file.read(1):
            if c == '\n':
                pos = file.tell()
                s = file.read(3)
                file.seek(pos)
                if s == '###':
                    break
            elif c == '\\':
                s = file.read(1)
                if s == '\\':
                    pass
                elif s == 'x':
                    c = chr(int(file.read(2), base=16))
                else:
                    raise SyntaxError(f'Unknown escape sequence \'{c}{s}\'')
            out.write(c.encode())
        return out.getvalue()

    def parse_key_value() -> tuple[str, bytes] | None:
        while (c := peek()) and c in '\n\t ':
            file.read(1)
        if not c:
            return None

        key = ''
        while (c := file.read(1)) and c not in '\n\t ':
            if c == ':':
                break
            key += c
        else:
            raise SyntaxError(f'Missing \':\' after key {key!r}')

        c = file.read(1)
        if c == '\n':
            value = parse_string()
        else:
            value = b''
            while (c := file.read(1)) and c != '\n':
                value += c.encode()

        return key, value

    values: list[dict[str, bytes]] = [{}]
    while True:
        while (c := peek()) and c in '\n\t ':
            file.read(1)
        if not c:  # EOF
            break
        accept('###')
        if peek() == '\n':
            file.read(1)
            continue
        accept(' ')

        if (k := parse_key_value()) is None:
            break
        # print(k)
        key, value = k
        del k

        if key == 'test_name' and values[-1]:
            values.append({})

        values[-1][key] = value

    assert values[-1]
    tests = []
    for value in values:
        value['name'] = value.pop('test_name').decode('utf-8')
        if 'compiler_return_code' in value:
            value['compiler_return_code'] = int(value['compiler_return_code'].decode())
        if 'run_program' in value:
            value['run_program'] = {b'true': True, b'false': False}[value['run_program']]
        print(value)
        tests.append(Test(**value))
    return tests


test_results: dict[int, list[TestReport]] = {}
for test_group_id, (test_group_filename, test_group_name) in test_groups.items():
    filename = os.path.join('tests', test_group_filename)
    with open(filename, 'r') as file:
        tests = parse_tests(file)
        for test in tests:
            test_results.setdefault(test_group_id, []).append(test.run())

successes = 0
failures: list[TestReportFailed] = []
for test_group_id, group_test_results in test_results.items():
    print(f'{test_group_id:03}: ', end='')
    for test_result in group_test_results:
        print(test_result.to_short_string(), end='')
        if type(test_result) is TestReportSucceeded:
            successes += 1
        elif type(test_result) is TestReportFailed:
            failures.append(test_result)
        else:
            raise AssertionError(test_result.__class__)
    print()

# print(tests)

print(f'Successes: {successes}')
print(f'Failures: {len(failures)}')
for failure in failures:
    print('-' * 70)
    print(failure.to_detailed_string())
