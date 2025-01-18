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


def check_types(ast: list[ast_.Func | ast_.Import | ast_.ImportFrom]) -> list['il.Op']:
    import il
    ir: list[il.Op] = []
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
            elif node.item == 'print':
                return ('print', Type(
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
                    ir.append(il.Operation(node.type, lhs, rhs))
                    # TODO: check if this cast is valid
                    return rhs

                if lhs != rhs:
                    error.print_error(f'type {lhs} does not match type {rhs} in operation {node.type}')

                ir.append(il.Operation(node.type, lhs, lhs))
                if node.type == ast_.OperationType.ADDITION:
                    return lhs
                if lhs.type != Types.INT:
                    error.print_error(f'operation {node.type} not allowed on type {lhs.type}')
                return lhs
            elif isinstance(node, ast_.FuncCall):
                for arg in node.args:
                    check_expr(arg)  # TODO: check arguments
                return_type = get_from_func_scope(node.function_name).subtype.return_type
                ir.append(il.FuncCall(node.function_name, return_type))
                return return_type
            elif isinstance(node, ast_.NumberLiteral):
                ir.append(il.ImmediateValue(il.TypeValue(Type(Types.INT, node), node.value)))
                return Type(Types.INT, node)
            elif isinstance(node, ast_.StringLiteral):
                t = Type(Types.STRING, node)
                ir.append(il.ImmediateValue(il.TypeValue(t, node.value)))
                return t
            elif isinstance(node, ast_.Variable):
                t = get_from_func_scope(node.variable_name)
                ir.append(il.GetFromFuncScope(node.variable_name, t))
                return t
            elif isinstance(node, ast_.Type):
                return Type.from_ast_type(node)
            elif isinstance(node, ast_.UnaryOperation):
                t = check_expr(node.rhs)
                if t.type != Types.INT:
                    error.print_error('Unary operation only accepts integers')
                ir.append(il.UnaryOperation(node.type, t, t))
                return t

            raise NotImplementedError(f'check_expr {node}')

        file_scope[node.func_name] = Type(
            Types.FUNC,
            node,
            FuncType(
                node.return_type,  # TODO: This is probably the wrong type
                [arg.type for arg in node.args.args]
            )
        )
        local_scope: scope = {}
        if node.body is None:
            raise Exception('cannot type check function without body')
        for sub_node in node.body.code:
            if isinstance(sub_node, ast_.VarDef):
                local_scope[sub_node.var_name] = Type.from_ast_type(sub_node.var_type)
            elif isinstance(sub_node, ast_.Expression):
                check_expr(sub_node)
                ir.append(il.Drop())
            elif isinstance(sub_node, ast_.VarAssignment):
                t = get_from_func_scope(sub_node.var_name)
                if sub_node.operation is not None and t.type == Types.STRING and sub_node.operation != ast_.OperationType.ADDITION:
                    error.print_error(f'operation {sub_node.operation} not allowed on type {t.type}')

                if sub_node.operation is not None:
                    ir.append(il.GetFromFuncScope(sub_node.var_name, t))
                expr_type = check_expr(sub_node.expr)
                if sub_node.operation is not None:
                    ir.append(il.Operation(sub_node.operation, t, t))

                assert type(t) is Type
                if t != expr_type:
                    error.print_error(f'trying to set variable with type {t.type} to type {expr_type}')
                ir.append(il.VarAssignment(sub_node.var_name, t))
                ir.append(il.Drop())
            else:
                raise NotImplementedError(sub_node)

        ir.append(il.ImmediateValue(il.TypeValue(Type(Types.VOID, None), None)))
        ir.append(il.Return())

    file_scope: scope = {}
    for node in ast:
        if isinstance(node, ast_.ImportFrom):
            func = check_import_from(node)
            file_scope[func[0]] = func[1]
        elif isinstance(node, ast_.Func):
            ir.append(il.FuncDef(node))
            check_func(node)
        else:
            raise NotImplementedError(node, type(node))

    # TODO: implement return statement
    # TODO: check return type

    # print(file_scope)
    # print(ir)
    # for i in ir:
    #     print('\t' + repr(i))
    return ir
