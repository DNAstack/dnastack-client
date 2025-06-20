class UnableToFindParameterError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class NoDefaultEngineError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
