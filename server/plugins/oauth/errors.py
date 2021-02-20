from App.base_restful import ApiException
from .error_codes import ErrorCodes


class UserNotFoundException(ApiException):
    status_code = 404
    description = "User Not Found"
    code = ErrorCodes.USER_NOT_FOUND


class UserAlreadyExistsException(ApiException):
    status_code = 403
    description = "User Already Exists"
    code = ErrorCodes.USER_ALREADY_EXISTS


class InvalidOperationException(ApiException):
    status_code = 400
    description = "Invalid Operation"
    code = ErrorCodes.INVALID_OPERATION


class InvalidPasswordException(ApiException):
    status_code = 401
    description = "Invalid Password"
    code = ErrorCodes.INVALID_PASSWORD


class InvalidUsernameSchemeException(ApiException):
    status_code = 403
    description = "Invalid Username Scheme"
    code = ErrorCodes.INVALID_PASSWORD_SCHEME


class InvalidPasswordSchemeException(ApiException):
    status_code = 403
    description = "Invalid Password"
    code = ErrorCodes.INVALID_PASSWORD_SCHEME


class DomainNotFoundException(ApiException):
    status_code = 404
    description = "Domain Not Found"
    code = ErrorCodes.DOMAIN_NOT_FOUND


class ScopeNotFoundException(ApiException):
    status_code = 404
    description = "Scope Not Found"
    code = ErrorCodes.SCOPE_NOT_FOUND
