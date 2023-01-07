from .rpc_error import ClientAlreadyStarted, ClientAlreadyStopped, InvalidUrl, RequestFailed, InvalidFile

class Errors(
    ClientAlreadyStarted,
    ClientAlreadyStopped,
    InvalidUrl,
    RequestFailed,
    InvalidFile,
):
    pass