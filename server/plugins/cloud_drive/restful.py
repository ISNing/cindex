import copy
import logging

from flask import request, Blueprint
from flask_restx import Resource, fields

from App import rest_util, util
from App.base_restful import RestResponse
from plugins.casbin.casbin import enforcer
from . import drive_util
from .api_config import api_conf
from .base_drive import ItemSchema, conf, models, item_model, drive_conf_payload_model
from .drive_util import import_drives, new_drive, get_drive
from .errors import DriveNotFoundException, InvalidResourceURIException, UpstreamAPIError, InvalidDriveConfException
from ..casbin.errors import NoPermissionAccessException

module_name = 'cloud_drive'
impl = 'cloud_drive'
description = 'A cloud drive restful api api blueprint model for flask.'
bp = cloud = Blueprint(__name__, __name__, url_prefix=conf['url_prefix'])
api = rest_util.gen_api(bp, api_conf)

logger = logging.getLogger(__name__)

rest_util.register_all_models_in_list(api, models)

new_ep_errs = {"post": [InvalidDriveConfException]}


@api.route('/new', endpoint='new_id_ep', methods=["POST"],
           doc={"post": {"responses": rest_util.gen_responses_doc(api, new_ep_errs["post"])}})
class NewDriveR(Resource):
    @staticmethod
    @api.expect(drive_conf_payload_model)
    @api.response(200, "Success Response",
                  RestResponse(None, "success").get_model_registered(api, "new_post_success_response"))
    def post():
        new_drive(util.get_post_data().get("data"))
        return RestResponse(None, 'success')


items_drive_id_key_ep_errs = {
    "get": [DriveNotFoundException, InvalidResourceURIException, UpstreamAPIError, NoPermissionAccessException],
    "delete": [DriveNotFoundException, InvalidResourceURIException, UpstreamAPIError, NoPermissionAccessException]}


@api.route('/items/<drive_id>/<key>', endpoint='items_drive_id_key_ep', methods=["GET", "DELETE"],
           doc={"params": {'drive_id': "The target drive\'s id",
                           'key': "The key part of the URI of target item(starts with \"id:/\" or \"path:/\")"},
                "get": {"responses": rest_util.gen_responses_doc(api, items_drive_id_key_ep_errs["get"])},
                "delete": {"responses": rest_util.gen_responses_doc(api, items_drive_id_key_ep_errs["delete"])}})
class ItemR(Resource):
    @staticmethod
    @api.response(200, "Success Response",
                  RestResponse(item_model).get_model_registered(api, "item_get_success_response"))
    def get(drive_id, key):
        uri = drive_util.gen_uri_by_key(drive_id, key)
        drive_util.enforce_item(uri)
        item = drive_util.get_item_by_uri(uri)
        result = ItemSchema().dump(item)
        result = drive_util.marshal_selects(result, request.args.get("select"))
        return RestResponse(result)

    # TODO: Add upload feature
    # def post(self, drive_id, key):
    #     pass
    @staticmethod
    @api.response(204, "Success Response",
                  RestResponse(None, "success").get_model_registered(api, "item_delete_success_response"))
    def delete(drive_id, key):
        uri = drive_util.gen_uri_by_key(drive_id, key)
        drive_util.enforce_item(uri)
        drive = get_drive(drive_id)
        drive.before_request()
        status = drive.delete_item(uri)
        return RestResponse(None, "success", status=status)


list_drive_id_ep_errs = {
    "get": [DriveNotFoundException, InvalidResourceURIException, UpstreamAPIError, NoPermissionAccessException]}
list_drive_id_key_ep_errs = {
    "get": [DriveNotFoundException, InvalidResourceURIException, UpstreamAPIError, NoPermissionAccessException]}


@api.route('/list/<drive_id>', endpoint='list_drive_id_ep', methods=["GET"],
           doc={"params": {'drive_id': "The target drive\'s id",
                           'key': "The key part of the URI of target item(starts with \"id:/\" or \"path:/\")"},
                "get": {"responses": rest_util.gen_responses_doc(api, list_drive_id_ep_errs["get"])}})
@api.route('/list/<drive_id>/<key>', endpoint='list_drive_id_key_ep', methods=["GET"],
           doc={"params": {'drive_id': "The target drive\'s id",
                           'key': "The key part of the URI of target item(starts with \"id:/\" or \"path:/\")"},
                "get": {"responses": rest_util.gen_responses_doc(api, list_drive_id_key_ep_errs["get"])}})
class ItemListR(Resource):
    @staticmethod
    @api.response(200, "Success Response",
                  RestResponse(fields.List(fields.Nested(item_model), required=True))
                  .get_model_registered(api, "list_get_success_response"))
    def get(drive_id, key='path:/'):
        uri = drive_util.gen_uri_by_key(drive_id, key)
        drive_util.enforce_item(uri)
        result = drive_util.get_item_list_by_uri(uri)
        item_list = []
        for item in result:
            if enforcer.cenforce(item.uri_id) or enforcer.cenforce(item.uri_path):
                item_dict = ItemSchema().dump(item)
                item_dict = drive_util.marshal_selects(item_dict, request.args.get("select"))
                item_list.append(item_dict)
        return RestResponse(item_list)


@bp.route('/<drive_id>/login')
def login(drive_id):
    drive = get_drive(drive_id)
    result = drive.login(copy.copy(request))
    return result


@bp.route('/<drive_id>/authorized')
def authorized(drive_id):
    drive = get_drive(drive_id)
    result = drive.authorized(copy.copy(request))
    return result


import_drives(conf['drives'])
