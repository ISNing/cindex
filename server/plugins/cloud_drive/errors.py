from App.base_restful import ApiException
from .error_codes import ErrorCodes


class DriveNotFoundException(ApiException):
    status_code = 404
    description = 'Drive Not Found'
    code = ErrorCodes.DRIVE_NOT_FOUND


class InvalidDriveConfException(ApiException):
    status_code = 400
    description = 'Invalid Drive Conf'
    code = ErrorCodes.INVALID_DRIVE_CONF


class InvalidResourceURIException(ApiException):
    status_code = 400
    description = 'Invalid Resource URI'
    code = ErrorCodes.INVALID_RESOURCE_URI


class UpstreamAPIError(ApiException):
    status_code = 500
    description = 'An error occurred when server contact with upstream api'
    code = ErrorCodes.UPSTREAM_API_ERROR
