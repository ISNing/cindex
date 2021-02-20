import os

from authlib.integrations.flask_oauth2 import current_token
from flask import Blueprint
from flask_restx import Resource, fields
from marshmallow import ValidationError
from sqlalchemy import and_

from App import util, rest_util
from App.base_restful import RestResponse
from App.errors import InvalidJSONSyntaxException
from plugins.casbin import perm_util
from plugins.casbin.perm_util import require_permission
from plugins.oauth import oauth_util
from .api_config import api_conf
from .models import db, Update, UpdateSchema
from .oauth_config import scopes, D_TAG
from .perm_config import perms

default_conf = {
    'url_prefix': '/updater'
}
conf = util.get_conf_checked('exthmui.updater.restful', default_conf)

module_name = 'exthmui_update'
impl = 'exTHmUI_Update'
description = 'A exthmui updater restful api blueprint module for flask.'
bp = Blueprint(module_name, module_name, url_prefix=conf['url_prefix'])
api = rest_util.gen_api(bp, api_conf)

require_oauth = oauth_util.gen_resource_protector(D_TAG)


def first_run():
    load_default_policy()


def load_default_policy():
    perm_util.add_policy_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), './default.csv')))


@bp.before_app_first_request
def create_table():
    db.create_all()


update_fields = {
    'id': fields.String(example="d287caa0c7b7aba365ecb9c6b818cab70bfbcc70c75e779ea489df487da04bcc", required=True),
    'name': fields.String(example="{os_name} 1.0", required=True),
    'device': fields.String(example="polaris", required=True),
    'packagetype': fields.String(default="full", enum=["full", "patch"]),
    'requirement': fields.Integer(default=0),
    'changelog': fields.String(example="VXBkYXRlJTIwdG8lMjBleFRIbVVJJTIwMS4w"),
    'timestamp': fields.Integer(example=1590764400, required=True),
    'filename': fields.String(example="ota-package.zip", required=True),
    'releasetype': fields.String(example="RELEASE", required=True),
    'size': fields.Integer(example="1024000000", required=True),
    'url': fields.String(example="https://example.com/ota-package.zip", required=True),
    'imageurl': fields.String(example="https://example.com/update_banner.png", default=""),
    'version': fields.String(example="1.0", required=True),
    'maintainer': fields.String(example="ISNing", required=True)
}
update_model = api.model("update", update_fields)
update_payload_fields = {"data": fields.Nested(update_model)}
update_payload_model = api.model("update_payload", update_payload_fields)
updates_list_payload_fields = {"data": fields.List(fields.Nested(update_model), required=True)}
updates_list_payload_model = api.model("updates_list_payload", updates_list_payload_fields)


def insert_update(u_conf):
    u = UpdateSchema().load(u_conf, session=db.session)
    db.session.add(u)
    db.session.commit()
    db.session.close()
    return u


def gen_updates_list(device, releasetype, version):
    if device:
        if releasetype:
            updates = db.session.query(Update).filter(and_(Update.device == device, Update.releasetype == releasetype,
                                                           Update.timestamp > version)).all()
        else:
            updates = db.session.query(Update).filter(and_(Update.device == device)).all()
    else:
        updates = db.session.query(Update).all()
    return updates


update_ep_errs = {"get": []}
update_id_ep_errs = {"get": []}


@api.route('/update', endpoint='update_ep', methods=["POST"],
           doc={"get": {"responses": rest_util.gen_responses_doc(api, update_ep_errs["get"])}})
@api.route('/update/<string:id>', endpoint='update_id_ep', methods=["GET", "POST", "DELETE"],
           doc={"params": {'id': "The update package\'s id"},
                "get": {"responses": rest_util.gen_responses_doc(api, update_id_ep_errs["get"])}})
class UpdateR(Resource):
    @api.response(200, "Success Response",
                  RestResponse(update_model).get_model_registered(api, "update_get_success_response"))
    def get(self, id):
        u = db.session.query(Update).filter(id=id).first()
        return RestResponse(u)

    @api.expect(update_payload_model)
    @api.response(200, "Success Response",
                  RestResponse(None, "success").get_model_registered(api, "update_post_success_response"))
    @require_oauth(scopes["UPDATES_WRITE"])
    @require_permission(perms["UPDATES_WRITE"])
    def post(self):
        print(current_token.user)
        try:
            data = util.get_post_data().get("data")
        except AttributeError:
            raise InvalidJSONSyntaxException()
        try:
            insert_update(data)
        except ValidationError as e:
            raise InvalidJSONSyntaxException(e.normalized_messages())
        return RestResponse(None, "success")

    @api.response(200, "Success Response",
                  RestResponse(update_model).get_model_registered(api, "update_get_success_response"))
    @require_oauth(scopes["UPDATES_WRITE"])
    @require_permission(perms["UPDATES_WRITE"])
    def delete(self, id):
        u = db.session.query(Update).filter(id == id).first()
        db.session.delete(u)
        return RestResponse(None, "success")


updates_ep_errs = {"get": []}
updates_device_ep_errs = {"get": []}
updates_device_releasetype_ep_errs = {"get": []}
updates_device_releasetype_version_ep_errs = {"get": []}


@api.route('/updates', endpoint='updates_ep', methods=["GET", "POST"],
           doc={"get": {"responses": rest_util.gen_responses_doc(api, updates_ep_errs["get"])}})
@api.route('/updates/<string:device>', endpoint='updates_device_ep', methods=["GET"],
           doc={"params": {'device': "The device\'s codename"},
                "get": {"responses": rest_util.gen_responses_doc(api, updates_device_ep_errs["get"])}})
@api.route('/updates/<string:device>/<string:releasetype>', endpoint='updates_device_releasetype_ep', methods=["GET"],
           doc={"params": {'device': "The device\'s codename",
                           'releasetype': "The release type of the packages requested",
                           'version': "Get all updates of this device after this timestamp"},
                "get": {"responses": rest_util.gen_responses_doc(api, updates_device_releasetype_ep_errs["get"])}})
@api.route('/updates/<string:device>/<string:releasetype>/<int:version>',
           endpoint='updates_device_releasetype_version_ep',
           methods=["GET"],
           doc={"params": {'device': "The device\'s codename",
                           'releasetype': "The release type of the packages requested",
                           'version': "Get all updates of this device after this timestamp"},
                "get": {
                    "responses": rest_util.gen_responses_doc(api, updates_device_releasetype_version_ep_errs["get"])}})
class UpdatesListR(Resource):
    @api.expect(updates_list_payload_model)
    @api.response(200, "Success Response",
                  RestResponse(None, "success")
                  .get_model_registered(api, "updates_post_success_response"))
    @require_oauth(scopes["UPDATES_WRITE"])
    @require_permission(perms["UPDATES_WRITE"])
    def post(self):
        data = util.get_post_data()
        try:
            data = data.get("data")
        except AttributeError:
            raise InvalidJSONSyntaxException()
        for update in data:
            try:
                insert_update(update)
            except ValidationError as e:
                raise InvalidJSONSyntaxException(e.normalized_messages())
        return RestResponse(None, "success")

    @staticmethod
    @api.response(200, "Success Response",
                  RestResponse(fields.List(fields.Nested(update_model)))
                  .get_model_registered(api, "updates_get_success_response"))
    @require_oauth(scopes["UPDATES_READ"], optional=True)
    @require_permission(perms["UPDATES_READ"])
    def get(device=None, releasetype=None, version=0):
        u_list = gen_updates_list(device, releasetype, version)
        u_list = (UpdateSchema().dump(u_list, many=True))
        return RestResponse(u_list)
