from enum import Enum, auto
from typing import NamedTuple


class Person(NamedTuple):
    name: str


class Shift(NamedTuple):
    name: str


class ShiftType(Enum):
    NORMAL = auto()
    SATURDAY = auto()
    SUNDAY = auto()
