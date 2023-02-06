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
        super().__init__(name, ret_type, args)
        self.library = library


class Library:
    def __init__(self, name):
        self.name = name
        self.functions = []  # TODO

    def __repr__(self):
        return "'" + 'library ' + "'" + self.name + "', " + str(self.functions) + "'"
