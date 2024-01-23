from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum, auto


class Scope(Enum):
    PRIVATE = auto()
    PUBLIC = auto()


@dataclass
class Node(ABC):
    def __new__(cls, *args, **kwargs):
        # https://stackoverflow.com/a/60669138
        if cls == Node or cls.__bases__[0] == Node:
            raise TypeError("Cannot instantiate abstract class.")
        return super().__new__(cls)


@dataclass
class Type(Node):
    children: List[Optional[Type]]


class BlockType(Enum):
    NORMAL = auto()
    PARENT = auto()
    GLOBAL = auto()


@dataclass
class Block(Node):
    type: BlockType
    code: List[Node]


@dataclass
class FuncArg(Node):
    type: Type
    name: str


@dataclass
class FuncArgs(Node):
    args: List[FuncArg]


@dataclass
class Func(Node):
    scope: Scope
    return_type: Type
    args: FuncArgs
    body: Block
