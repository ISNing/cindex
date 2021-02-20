from App.base_restful import ApiException


class NoPermissionAccessException(ApiException):
    status_code = 403
    description = "You have no permission accessing this resource"
    code = "no_permission"
