class Sio2ToolsException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class SessionObtainFailed(Sio2ToolsException):
    def __init__(self, message):
        super().__init__(message or "Failed to obtain session")


class NoPasswordProvided(Sio2ToolsException):
    def __init__(self, message):
        super().__init__(message or "No password provided")
