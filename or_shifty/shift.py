from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto
from typing import Any, Dict

from or_shifty.person import Person


@dataclass(frozen=True)
class Shift:
    name: str
    shift_type: "ShiftType"
    day: date

    @classmethod
    def from_json(cls, serialised: Dict[str, Any]) -> "Shift":
        return Shift(
            name=serialised["name"],
            shift_type=ShiftType.from_json(serialised["type"]),
            day=datetime.fromisoformat(serialised["day"]).date(),
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.shift_type.to_json(),
            "day": self.day.isoformat(),
        }

    def assign(self, person: Person) -> "AssignedShift":
        return AssignedShift(
            name=self.name, shift_type=self.shift_type, day=self.day, person=person,
        )


@dataclass(frozen=True)
class AssignedShift(Shift):
    person: Person

    def __str__(self):
        st_len = max(len(st.name) for st in ShiftType)
        shift_type = self.shift_type.name.lower()
        return f"{str(self.day)} ({self.name} - {shift_type:<{st_len}}) - {self.person.name}"

    @classmethod
    def from_json(cls, serialised: Dict[str, Any]) -> "AssignedShift":
        return AssignedShift(
            name=serialised["name"],
            shift_type=ShiftType.from_json(serialised["type"]),
            day=datetime.fromisoformat(serialised["day"]).date(),
            person=Person(name=serialised["person"]),
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.shift_type.to_json(),
            "day": self.day.isoformat(),
            "person": self.person.name,
        }

    def unassigned(self) -> Shift:
        return Shift(name=self.name, shift_type=self.shift_type, day=self.day)


class ShiftType(Enum):
    STANDARD = auto()
    SPECIAL_A = auto()
    SPECIAL_B = auto()

    @classmethod
    def from_day(cls, day: date):
        if day.weekday() == 5:
            return ShiftType.SATURDAY
        if day.weekday() == 6:
            return ShiftType.SUNDAY
        return ShiftType.WEEKDAY

    def is_of_type(self, day: date, bank_holidays: Dict[date, "ShiftType"]):
        if day in bank_holidays:
            return self is bank_holidays[day]
        if day.weekday() == 5:
            return self is ShiftType.SATURDAY
        if day.weekday() == 6:
            return self is ShiftType.SUNDAY
        return self is ShiftType.WEEKDAY

    @classmethod
    def from_json(cls, serialised) -> "ShiftType":
        serialised = serialised.lower()
        if serialised == "standard":
            return ShiftType.STANDARD
        elif serialised == "special_a":
            return ShiftType.SPECIAL_A
        elif serialised == "special_b":
            return ShiftType.SPECIAL_B
        else:
            assert False, f"Unknown shift type {serialised}"

    def to_json(self) -> str:
        return self.name.lower()
