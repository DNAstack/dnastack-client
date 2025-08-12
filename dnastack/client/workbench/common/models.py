from enum import Enum


class State(str, Enum):
    PREPROCESSING = "PREPROCESSING"
    UNKNOWN = "UNKNOWN"
    QUEUED = "QUEUED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELING = "CANCELING"
    COMPLETE = "COMPLETE"
    EXECUTOR_ERROR = "EXECUTOR_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CANCELED = "CANCELED"
    COMPLETE_WITH_ERRORS = "COMPLETE_WITH_ERRORS"
    PREPROCESSING_ERROR = "PREPROCESSING_ERROR"
    NOT_PROCESSED = "NOT_PROCESSED"

    def is_error(self) -> bool:
        return self in [State.COMPLETE_WITH_ERRORS, State.EXECUTOR_ERROR, State.SYSTEM_ERROR]

    def is_terminal(self) -> bool:
        return self in [State.COMPLETE, State.COMPLETE_WITH_ERRORS, State.CANCELED, State.EXECUTOR_ERROR,
                        State.SYSTEM_ERROR]


class CaseInsensitiveEnum(Enum):
    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")
