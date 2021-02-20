from App.base_restful import ApiException


class NotFoundException(ApiException):
    code = 404
    description = 'fuck u'
