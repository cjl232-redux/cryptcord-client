class MissingFernetKey(Exception):
    pass

class ResponseError(Exception):
    pass

class ResponseClientError(ResponseError):
    pass

class ResponseServerError(ResponseError):
    pass

class ResponseUnknownError(ResponseError):
    pass