from enum import StrEnum


class InterfaceFields(StrEnum):
    ENDPOINT = 'endpoint'
    MA = 'ma'
    CHANGE = 'change'
    MA_OF_CHANGE = 'ma_of_change'
    CUM_CHANGE = 'cum_change'
    MEAN = 'mean'
    STD = 'std'