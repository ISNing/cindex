from App.base_restful import ApiException


class NotFullyImplementedException(Exception):
    pass


class NotModuleException(NotFullyImplementedException):
    pass


class MultipleImplementException(Exception):
    pass


class InvalidJSONSyntaxException(ApiException):
    status_code = 400
    description = "Invalid JSON Syntax"
    code = "invalid_json_syntax"
