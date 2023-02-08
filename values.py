class Function:
    def __init__(self, name, ret_type, args, mods: list):
        self.name = name
        self.ret_type = ret_type
        self.args = args

        self.mods = mods
        self.body = []

    def __repr__(self):
        return "'function '" + self.name + "', " + str(self.ret_type) + ", " + str(self.args) + ' mods: ' + str(self.mods) + "'"


class LibraryFunction(Function):
    def __init__(self, name, ret_type, args, library):
        """used in for example 'from A import B', this would be B"""
        super().__init__(name, ret_type, args, [])
        self.library = library


class Library:
    def __init__(self, name):
        self.name = name
        self.functions = []  # TODO

    def __repr__(self):
        return "'" + 'library ' + "'" + self.name + "', " + str(self.functions) + "'"


class Constant:
    def __init__(self, name, types, value):
        self.name = name
        self.types = types
        self.value = value

    def __repr__(self):
        return "'constant " + str(self.types) + "'" + self.name + "', = '" + str(self.value) + "'"


class Variable:
    def __init__(self, name, t, value=None):
        self.name = name
        self.type = t

        self.value = value

    def __repr__(self):
        return "variable " + str(self.type) + " '" + self.name + "'"
