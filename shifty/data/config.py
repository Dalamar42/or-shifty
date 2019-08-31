from typing import NamedTuple


class Config(NamedTuple):
    min_days_between_ops: int
    min_weekends_between_weekend_ops: int

    @classmethod
    def build(cls, min_days_between_ops=3, min_weekends_between_weekend_ops=2):
        return cls(
            min_days_between_ops=min_days_between_ops,
            min_weekends_between_weekend_ops=min_weekends_between_weekend_ops,
        )
