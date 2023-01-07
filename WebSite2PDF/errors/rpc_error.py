class ClientAlreadyStarted(Exception):
    def __init__(self, customText: str = "Client has already been started!") -> None:
        super().__init__(customText)

class ClientAlreadyStopped(Exception):
    def __init__(self, customText: str = "Client has already been stopped!") -> None:
        super().__init__(customText)

class InvalidUrl(Exception):
    def __init__(self, customText: str = "Invalid URL or Site unavailable.") -> None:
        super().__init__(customText)

class InvalidFile(Exception):
    def __init__(self, customText: str = "Invalid File or Incorrect File Path.") -> None:
        super().__init__(customText)

class RequestFailed(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(f"Something went wrong: {reason}")