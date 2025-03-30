from __future__ import annotations

import enum
from abc import ABC
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum, auto


class Scope(Enum):
    PRIVATE = auto()
    PUBLIC = auto()


@dataclass
class Node(ABC):
    # def __new__(cls, *args, **kwargs):
    #     # https://stackoverflow.com/a/60669138
    #     if cls == Node or cls.__bases__[0] == Node:
    #         raise TypeError("Cannot instantiate abstract class.")
    #     return super().__new__(cls)
    pass


@dataclass
class Type(Node):
    type: List[SubType]


@dataclass
class SubType(Node):
    type: str
    children: List[Type]


class BlockType(Enum):
    NORMAL = auto()
    PARENT = auto()
    GLOBAL = auto()


@dataclass
class Block(Node):
    type: BlockType
    code: List[Node]


@dataclass
class FuncArg(Node):  # TODO: this is the same as VarDef
    name: str
    type: Type


@dataclass
class FuncArgs(Node):
    args: List[FuncArg]


@dataclass
class Func(Node):
    scope: Scope
    return_type: Type
    func_name: str
    args: FuncArgs
    body: Block | None


@dataclass
class Import(Node):
    module: str
    as_: str | None


@dataclass
class ImportFrom(Node):
    module: str
    item: str
    as_: str | None


@dataclass
class VarDef(Node):
    var_name: str
    var_type: Type


@dataclass
class ClassDef(Node):
    class_name: str
    var_defs: list[VarDef]


@dataclass
class VarAssignment(Node):
    var_name: str
    expr: Expression
    operation: OperationType | None


class Expression(Node, ABC):
    pass


class OperationType(Enum):
    PIPE = enum.auto()
    ASSIGN = enum.auto()

    LOGICAL_XOR = enum.auto()
    LOGICAL_OR = enum.auto()
    LOGICAL_AND = enum.auto()
    LOGICAL_NOT = enum.auto()

    CONTAINS = enum.auto()
    NOT_CONTAINS = enum.auto()

    COMP_LT = enum.auto()
    COMP_GT = enum.auto()
    COMP_GE = enum.auto()
    COMP_LE = enum.auto()
    COMP_EQ = enum.auto()
    COMP_NE = enum.auto()

    BINARY_OR = enum.auto()
    BINARY_XOR = enum.auto()
    BINARY_AND = enum.auto()

    BITSHIFT_LEFT = enum.auto()
    BITSHIFT_RIGHT = enum.auto()

    ADDITION = enum.auto()
    SUBTRACTION = enum.auto()
    MULTIPLICATION = enum.auto()
    DIVISION = enum.auto()
    FLOOR_DIVISION = enum.auto()
    MODULO = enum.auto()
    FLOOR_MODULO = enum.auto()

    EXPONENT = enum.auto()

    CAST = enum.auto()


@dataclass
class Operation(Expression):
    lhs: Expression
    rhs: Expression  # TODO: when casting this could be a Type so do not cast using this
    type: OperationType


class UnaryOperationType(enum.Enum):
    NEGATE = enum.auto()
    BINARY_NOT = enum.auto()


@dataclass
class UnaryOperation(Expression):
    rhs: Expression
    type: UnaryOperationType


@dataclass
class ExprBlock(Expression):
    body: Block
    return_: Expression | None


@dataclass
class IfElse(Expression):
    condition: Expression
    if_: ExprBlock
    else_: ExprBlock | None


class Literal(Expression, ABC):
    pass


@dataclass
class NumberLiteral(Literal):
    value: int | float


@dataclass
class StringLiteral(Literal):
    value: str


@dataclass
class Variable(Literal):  # TODO: should this inherit from Literal?
    variable_name: str


@dataclass
class FuncCall(Expression):
    function_name: str
    args: list[Expression]


@dataclass
class If(Expression):
    condition: Expression
    if_: Expression
    else_: Optional[Expression]


# @dataclass
# class Assignment(Statement):  # TODO: Statement
#     lhs: Expression
#     rhs: Expression
#     op_type: Optional[OperationType]  # e.g. ===, =>=, =!=
