from abc import ABCMeta
from typing import Dict

from ortools.constraint_solver.pywrapcp import IntVar
from ortools.sat.python.cp_model import LinearExpr

from or_shifty.config import Config
from or_shifty.indexer import Idx
from or_shifty.shift import ShiftType


class Objective(metaclass=ABCMeta):
    def objective(self, assignments: Dict[Idx, IntVar], data: Config) -> LinearExpr:
        pass


class RankingWeight(Objective):
    ADDITIONAL_SHIFTS_WEIGHT = 100
    RANKING_WEIGHT = 1

    def objective(self, assignments: Dict[Idx, IntVar], data: Config) -> LinearExpr:
        # Compute the ranking weight for each shift_type. The coefficient is to discourage optimising one
        # shift type at the expense of another
        return LinearExpr.Sum(
            self._ranking_weight_for_shift_type(assignments, data, shift_type)
            for shift_type in ShiftType
        )

    def _ranking_weight_for_shift_type(
        self, assignments: Dict[Idx, IntVar], data: Config, shift_type: ShiftType
    ) -> LinearExpr:
        people_ranking = self._rank_people(data, shift_type)

        weights = self._assign_weights(data, people_ranking)

        # Multiply each person/person_shift assignment to a day_shift of the selected shift_type
        # (which should be either 0 or 1) with the corresponding weight and return the sum
        expressions = []
        coefficients = []
        for (person, person_shift), weight in weights.items():
            indices_to_include = [
                index
                for index in data.indexer.iter(
                    person_filter=person, person_shift_filter=person_shift
                )
                if index.day_shift.shift_type is shift_type
            ]
            expressions.append(
                sum(assignments[index.idx] for index in indices_to_include)
            )
            coefficients.append(weight)

        return LinearExpr.ScalProd(expressions, coefficients)

    def _rank_people(self, data, shift_type):
        # Rank people based on
        # 1. how many shifts they have done (DESC)
        # 2. how recently they have been on shift (ASC)
        # 3. the person's name to ensure there is a total ordering
        people = list(data.shifts_by_person.keys())
        historical_shifts = {
            person: data.history_metrics.num_of_shifts.get(shift_type, {}).get(
                person, 0
            )
            for person in people
        }
        free_days_since_last = {
            person: data.now - data.history_metrics.date_last_on_shift[person]
            for person in people
        }
        return sorted(
            people,
            key=lambda p: (historical_shifts[p], -free_days_since_last[p], p.name,),
            reverse=True,
        )

    def _assign_weights(self, data, people_ranking):
        shift_change_marker = object()

        # Rank people shifts s.t. everyone's first shift is ranked higher than anyone's second shift and so on
        people_shifts_ranking = []
        for person_shift_idx in reversed(range(data.max_shifts_per_person)):
            for person in people_ranking:
                people_shifts_ranking.append(
                    (person, data.shifts_by_person[person][person_shift_idx])
                )
            people_shifts_ranking.append(shift_change_marker)

        # Assign a weight to every person/shift to encourage assigning to pairs higher up in the ranking
        # first. The additional shifts weight when changing shifts ensures that we penalise more heavily
        # assigning someone to a second or third shift
        next_weight = 0
        weights = {}
        for entry in people_shifts_ranking:
            if entry is shift_change_marker:
                next_weight += self.ADDITIONAL_SHIFTS_WEIGHT
                continue

            weights[entry] = next_weight
            next_weight += self.RANKING_WEIGHT

        return weights


OBJECTIVE_FUNCTIONS = {objective.__name__: objective for objective in (RankingWeight,)}
