
class BitMEXWebsocketApiError(Exception):
    """Raised when an error message is returned from the api.
    
    :param int status: The http status that matches the error type.
    :param string message: The error description.

    """
    def __init__(self, status, message) -> None:
        self.status = status
        super().__init__(message)
        
    pass