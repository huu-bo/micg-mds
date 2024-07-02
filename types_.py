from __future__ import annotations
import enum
import dataclasses

import ast_
import error

# bootstrapping compiler does not support embedded scopes


class Types(enum.Enum):
    INT = enum.auto()
    STRING = enum.auto()
    VOID = enum.auto()
    ARRAY = enum.auto()
    FUNC = enum.auto()


@dataclasses.dataclass
class Type:
    type: Types
    node: ast_.Node | None = dataclasses.field(compare=False)
    subtype: Types | FuncType | None = None

    def __post_init__(self):
        if self.subtype is not None:
            if self.type != Types.ARRAY and self.type != Types.FUNC:
                error.print_error('bootstrapping compiler does not support generic typing')

    @classmethod
    def from_ast_type(cls, ast_type: ast_.Type) -> Type:  # TODO: support ast_.Func
        if len(ast_type.type) != 1:
            raise NotImplementedError()
        type_name = ast_type.type[0].type
        # TODO: ARRAY
        if type_name == 'str':
            t = Types.STRING
        else:
            t = getattr(Types, type_name.swapcase())

        return Type(
            t,
            ast_type
        )


@dataclasses.dataclass
class FuncType:
    return_type: Type
    args: list[Type]


def check_types(ast: list[ast_.Func | ast_.Import | ast_.ImportFrom]) -> None:
    scope = dict[str, Type]

    def check_import_from(node: ast_.ImportFrom) -> tuple[str, Type]:
        if node.module == 'console':
            if node.item == 'println':
                # return ('println', ast_.Func(
                #     ast_.Scope.PUBLIC,
                #     ast_.Type([]),
                #     ast_.FuncArgs(
                #         [ast_.FuncArg('line', ast_.Type([ast_.SubType('str', [])]))]
                #     ),
                #     None))
                return ('println', Type(
                    Types.FUNC,
                    node,
                    FuncType(
                        Type(Types.VOID, None),
                        [Type(Types.STRING, None)]
                    )
                ))
            else:
                raise AttributeError(f"{node.module}.{node.item}")
        else:
            raise ModuleNotFoundError(node.module)

    def check_func(node: ast_.Func) -> None:
        def get_from_func_scope(literal: str) -> Type:
            if literal in local_scope:
                return local_scope[literal]
            elif literal in file_scope:
                return file_scope[literal]
            else:
                error.print_error(f'unknown literal {literal}')

        def check_expr(node: ast_.Expression) -> Type:
            if isinstance(node, ast_.Operation):
                lhs = check_expr(node.lhs)
                rhs = check_expr(node.rhs)
                # cast and add
                if node.type == ast_.OperationType.CAST:
                    # TODO: check if this cast is valid
                    return rhs

                if lhs != rhs:
                    error.print_error(f'type {lhs} does not match type {rhs} in operation {node.type}')

                if node.type == ast_.OperationType.ADDITION:
                    return lhs
                if lhs.type != Types.INT:
                    error.print_error(f'operation {node.type} not allowed on type {lhs.type}')
                return lhs
            elif isinstance(node, ast_.FuncCall):
                # TODO: check arguments
                return get_from_func_scope(node.function_name).subtype.return_type
            elif isinstance(node, ast_.NumberLiteral):
                return Type(Types.INT, node)
            elif isinstance(node, ast_.StringLiteral):
                return Type(Types.STRING, node)
            elif isinstance(node, ast_.Variable):
                return get_from_func_scope(node.variable_name)
            elif isinstance(node, ast_.Type):
                return Type.from_ast_type(node)

            raise NotImplementedError(f'check_expr {node}')

        local_scope: scope = {}
        if node.body is None:
            raise Exception('cannot type check function without body')
        for sub_node in node.body.code:
            if isinstance(sub_node, ast_.VarDef):
                local_scope[sub_node.var_name] = Type.from_ast_type(sub_node.var_type)  # TODO: this uses ast_.Type, not Type
            elif isinstance(sub_node, ast_.Expression):
                print(check_expr(sub_node))
            elif isinstance(sub_node, ast_.VarAssignment):
                t = get_from_func_scope(sub_node.var_name)
                if sub_node.operation is not None and t.type == Types.STRING and sub_node.operation != ast_.OperationType.ADDITION:
                    error.print_error(f'operation {sub_node.operation} not allowed on type {t.type}')
                expr_type = check_expr(sub_node.expr)
                assert type(t) is Type
                if t != expr_type:
                    error.print_error(f'trying to set variable with type {t.type} to type {expr_type}')
            else:
                raise NotImplementedError(sub_node)

    file_scope: scope = {}
    for node in ast:
        if isinstance(node, ast_.ImportFrom):
            func = check_import_from(node)
            file_scope[func[0]] = func[1]
        elif isinstance(node, ast_.Func):
            check_func(node)
        else:
            raise NotImplementedError(node, type(node))

    print(file_scope)
    raise NotImplementedError()
