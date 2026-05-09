class BdUtilsError(Exception):
    """Base package error."""


class WidgetNotDefinedError(BdUtilsError):
    pass


class SecretNotDefinedError(BdUtilsError):
    pass


class NotebookExit(BdUtilsError):
    def __init__(self, value: str):
        super().__init__(value)
        self.value = value
