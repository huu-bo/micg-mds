from __future__ import annotations

import dataclasses
import abc

import ast_
import types_


@dataclasses.dataclass
class Op(abc.ABC):
    pass


@dataclasses.dataclass
class Import(Op):
    # Name
    # Import
    pass


@dataclasses.dataclass
class Operation(Op):
    # 2
    # 1
    op_type: ast_.OperationType
    from_type: types_.Type
    to_type: types_.Type


@dataclasses.dataclass
class UnaryOperation(Op):
    # 1
    # 1
    op_type: ast_.UnaryOperationType
    from_type: types_.Type
    to_type: types_.Type


@dataclasses.dataclass
class ImmediateValue(Op):
    # 0
    # 1
    value: TypeValue


@dataclasses.dataclass
class TypeValue:  # assumes the value is of type type
    type: types_.Type
    # Func Type is not possible as an immediate
    value: int | str | None | list


@dataclasses.dataclass
class FuncCall(Op):
    # N: args
    # Return value
    func_name: str


@dataclasses.dataclass
class VarAssignment(Op):
    # 1
    # 1
    var_name: str
    var_type: types_.Type


@dataclasses.dataclass
class Drop(Op):
    # 1
    # 0
    pass


@dataclasses.dataclass
class GetFromFuncScope(Op):
    # 0
    # 1
    var_name: str
    var_type: types_.Type


@dataclasses.dataclass
class FuncDef(Op):
    # 0
    # 0
    metadata: ast_.Func


@dataclasses.dataclass
class Return(Op):
    # 1
    # -
    pass
