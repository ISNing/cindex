import json

from flask import jsonify, Response, request
from flask_restx import Api, fields, marshal_with, Model, Resource
# noinspection PyProtectedMember
from werkzeug._compat import integer_types, text_type
from werkzeug.datastructures import Headers
from werkzeug.exceptions import HTTPException
from werkzeug.utils import get_content_type


# noinspection PyShadowingBuiltins
class CApi(Api):
    def __init__(self, app, version, title, description, terms_url, license, license_url, contact, contact_url,
                 contact_email, authorizations, security, doc, default_id, default, default_label, validate, tags,
                 prefix, ordered, default_mediatype, decorators, catch_all_404s, serve_challenge_on_401, format_checker,
                 **kwargs):
        super(CApi, self).__init__(app, version, title, description, terms_url, license, license_url, contact,
                                   contact_url, contact_email, authorizations, security, doc, default_id, default,
                                   default_label, validate, tags, prefix, ordered, default_mediatype, decorators,
                                   catch_all_404s, serve_challenge_on_401, format_checker, **kwargs)
        import os
        api = self

        # noinspection PyUnusedLocal
        @self.route(os.path.join(doc, "postman.json"), doc=False)
        class PostMan(Resource):
            @staticmethod
            def get():
                urlvars = False  # Build query strings in URLs
                swagger = True  # Export Swagger specifications
                return api.as_postman(urlvars=urlvars, swagger=swagger)

    def handle_error(self, e):
        from App import rest_util
        error = rest_util.gen_api_e_from_e(e)
        return error.get_body(), error.status_code


class RestResponse(Response):
    # noinspection PyMissingConstructor
    def __init__(
            self,
            data=None,
            message=None,
            status=None,
            headers=None,
            mimetype="application/json",
            content_type="application/json",
            direct_passthrough=False,
    ):
        if isinstance(headers, Headers):
            self.headers = headers
        elif not headers:
            self.headers = Headers()
        else:
            self.headers = Headers(headers)

        if content_type is None:
            if mimetype is None and "content-type" not in self.headers:
                mimetype = self.default_mimetype
            if mimetype is not None:
                mimetype = get_content_type(mimetype, self.charset)
            content_type = mimetype
        if content_type is not None:
            self.headers["Content-Type"] = content_type
        if status is None:
            status = self.default_status
        if isinstance(status, integer_types):
            self.status_code = status
        else:
            self.status = status

        self.direct_passthrough = direct_passthrough
        self._on_close = []

        self.r_message = message
        self.r_data = data
        self.set_data(data)

    def set_data(self, data):
        """Sets a new string as response.  The value set must be either a
        unicode or bytestring.  If a unicode string is set it's encoded
        automatically to the charset of the response (utf-8 by default).

        .. versionadded:: 0.9
        """
        # if an unicode string is set, it's encoded directly so that we
        # can set the content length
        if isinstance(data, text_type):
            data = data.encode(self.charset)
        elif isinstance(data, (bytes, bytearray)):
            data = bytes(data)
        self.r_data = data
        if isinstance(self.r_data, Model) or (self.r_data.__class__.__name__ in dir(fields)):
            return
        resp = json.dumps(self.get_dict()).encode(self.charset)
        self.response = [resp]
        if self.automatically_set_content_length:
            self.headers["Content-Length"] = str(len(resp))

    def get_model(self=None, name="response"):
        if self is None:
            d = fields.Raw
        elif isinstance(self.r_data, Model):
            d = fields.Nested(self.r_data)
        elif self.r_data.__class__.__name__ in dir(fields):
            d = self.r_data
        else:
            d = fields.Raw(example=self.r_data)
        return Model(name, {
            "code": fields.Integer(example=self.status_code if self else None),
            "message": fields.String(example=self.r_message if self else None),
            "data": d
        })

    def get_model_registered(self, api, name="response"):
        api.models[name] = self.get_model(name)
        return api.models[name]

    @marshal_with(get_model())
    def get_dict(self):
        return {
            "code": self.status_code,
            "message": self.r_message,
            "data": self.r_data
        }


class ApiException(HTTPException):
    code: str = None
    status_code: int = None
    traceback: str = None

    def __init__(self, message=None, detail=None):
        if isinstance(message, Exception):
            from App import rest_util
            if isinstance(message, HTTPException) and not isinstance(message, ApiException):
                self.status_code = message.code
            e = rest_util.gen_api_e_from_e(message)
            message = e.message
            detail = e.detail
        self.status_code = self.status_code if self.status_code is not None else 500
        self.message = message
        self.detail = detail

    def get_body(self, environ=None):
        """Get the HTML body."""
        return jsonify(self.get_resp_dict())

    def get_models(self=None):
        model_e = Model((self.code if self else "response") + "_error_part", {
            "code": fields.String(example=self.code if self else None),
            "name": fields.String(example=self.get_name() if self else None),
            "request": fields.String(example="[...] -> https://..."),
            "description": fields.String(example=self.description if self else None),
            "detail": fields.Raw,
            "traceback": fields.String(
                example="Traceback from server, will only show when debug mode was enabled." if self else None)
        })
        model_r = Model(self.code if self else "response", {
            "code": fields.Integer(example=self.status_code if self else None),
            "message": fields.String(example=self.message if self else None),
            "error": fields.Nested(model_e, skip_none=True)
        })
        return [model_e, model_r]

    @marshal_with(get_models()[1])
    def get_resp_dict(self):
        return {
            "code": self.status_code,
            "message": self.message if self.message else self.status_name,
            "data": None,
            "error": self.get_err_dict()
        }

    @marshal_with(get_models()[0], skip_none=True)
    def get_err_dict(self, environ=None):
        """Get the Dict."""
        d = {
            "code": self.code,
            "name": self.get_name(),
            "request": "[" + request.method + "] >> " + request.url,
            "description": self.get_description(environ),
            "detail": self.detail,
            "traceback": self.traceback
        }
        return d

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]

    def get_description(self, environ=None):
        """Get the description."""
        return str(self.description)

    def get_name(self):
        return str(self.__class__.__name__)

    @property
    def status_name(self):
        """The status name."""
        from werkzeug import http
        return http.HTTP_STATUS_CODES.get(self.status_code, "Unknown Error")

    name = None


class ServerException(ApiException):
    status_code = 500
    code = "internal_server_error"
    description = "Unknown server error..."
