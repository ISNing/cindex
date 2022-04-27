from App.base_restful import ApiException


class NoPermissionAccessException(ApiException):
    status_code = 403
    description = "You have no permission accessing this resource"
    code = "no_permission"


class DomainNotFoundException(ApiException):
    status_code = 404
    description = "Domain Not Found"
    code = "domain_not_found"


class PermissionNotFoundException(ApiException):
    status_code = 404
    description = "Permission Not Found"
    code = "permission_not_found"
