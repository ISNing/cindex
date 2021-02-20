from App.base_restful import ApiException


class InvalidDataException(ApiException):
    status_code = 400
    description = "Invalid Data"
    code = 'invalid_data'


class UpdateAlreadyExistsException(ApiException):
    status_code = 403
    description = "Update Already Exists"
    code = 'update_already_exists'


class UpdateNotFoundException(ApiException):
    status_code = 404
    description = "Update Not Found"
    code = "update_not_found"


class DomainNotFoundException(ApiException):
    status_code = 404
    description = "Domain Not Found"
    code = "domain_not_found"


class PermissionNotFoundException(ApiException):
    status_code = 404
    description = "Permission Not Found"
    code = "permission_not_found"
