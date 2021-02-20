import json
import logging
import traceback
from json.decoder import JSONDecodeError

from flask_restx import utils
from werkzeug.exceptions import HTTPException

from App.base_restful import CApi, ApiException, ServerException

logger = logging.getLogger(__name__)


def gen_api(app, conf: dict, **kwargs):
    return CApi(app, version=conf.get("version", "1.0"), title=conf.get("title"), description=conf.get("description"),
                terms_url=conf.get("terms_url"), license=conf.get("license"), license_url=conf.get("license_url"),
                contact=conf.get("contact"), contact_url=conf.get("contact_url"),
                contact_email=conf.get("contact_email"), authorizations=conf.get("authorizations"),
                security=conf.get("security"), doc=conf.get("doc", "/docs/"),
                default_id=conf.get("default_id", utils.default_id), default=conf.get("default", "default"),
                default_label=conf.get("default_label", "Default namespace"), validate=conf.get("validate"),
                tags=conf.get("tags"), prefix=conf.get("prefix", ""), ordered=conf.get("ordered", False),
                default_mediatype=conf.get("default_mediatype", "application/json"), decorators=conf.get("decorators"),
                catch_all_404s=conf.get("catch_all_404s", False),
                serve_challenge_on_401=conf.get("serve_challenge_on_401", False),
                format_checker=conf.get("format_checker"), kwargs=kwargs)


def gen_api_e_from_e(e):
    if isinstance(e, ApiException):
        error = e
    elif isinstance(e, HTTPException):
        error = ApiException()
        error.__class__.__name__ = e.name
        try:
            error.detail = json.loads(e.get_body())
        except JSONDecodeError:
            error.detail = None
        error.status_code = e.code
        error.description = e.description
    else:
        from flask import current_app
        error = ServerException()
        if current_app.config["DEBUG"]:
            error.traceback = repr(e) + '\n' + str(traceback.format_exc())
            error.description = str(e)
            logger.warning(error.traceback)
    return error


def gen_model_from_api_e(api, e):
    err = e("messages...")
    models = err.get_models()
    for i in models:
        api.models[i.name] = i
    return err.status_code, (err.get_name(), models[1])


def gen_models_from_api_e(api, exceptions: list):
    models = []
    for e in exceptions:
        models.append(gen_model_from_api_e(api, e))
    return models


def gen_responses_doc(api, exceptions):
    responses = {}
    for e in exceptions:
        code, val = gen_model_from_api_e(api, e)
        responses[str(code)] = val
    return responses


def register_all_models_in_list(api: CApi, lis: list):
    for model in lis:
        api.models[model.name] = model

# def gen_response_doc(api, e):
#     status_code, name, model = gen_model_from_api_e(api, e)
#     return api.doc(get={"responses": {str(status_code): (name, model)}})
#
#
# def gen_responses_decorator(api, exceptions):
#     decs = []
#     for e in exceptions:
#         decs.append(gen_response_doc(api, e))
#     from App.util import composed
#     return composed(decs)
