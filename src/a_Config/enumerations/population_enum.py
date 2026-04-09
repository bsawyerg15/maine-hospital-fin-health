from enum import StrEnum

class Population(StrEnum):
    TOTAL = 'total'
    OPERATIONAL = 'non-failed'
    FAILED = 'failed'