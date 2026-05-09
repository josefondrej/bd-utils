class BdUtilsError(Exception):
    """Base package error."""


class WidgetNotDefinedError(BdUtilsError):
    """Raised when a requested widget is not defined."""

    pass


class SecretNotDefinedError(BdUtilsError):
    """Raised when a requested secret is not defined."""

    pass


class NotebookExit(BdUtilsError):
    """Exception raised to exit a notebook.

    Attributes:
        value (str): The exit value.
    """

    def __init__(self, value: str):
        super().__init__(value)
        self.value = value
