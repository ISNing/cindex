import os

from flask import Blueprint
from flask_restx import Resource, fields

from App import rest_util, util
from App.base_restful import RestResponse
from App.errors import InvalidJSONSyntaxException
from plugins.exthmui.updater.errors import PermissionNotFoundException, DomainNotFoundException
from plugins.oauth import oauth_util
from . import casbin, perm_util
from .api_config import api_conf
from .casbin import enforcer, conf
from .oauth_config import D_TAG, scopes
from .perm_config import perms
from .perm_util import require_permission

impl = "casbin"
module_name = 'casbin'
description = 'A casbin permission control blueprint module for flask.'
bp = Blueprint(module_name, module_name, url_prefix=conf['url_prefix'],
               template_folder=os.path.dirname(__file__) + "/templates",
               static_folder=os.path.dirname(__file__) + "/static", static_url_path="/")

api = rest_util.gen_api(bp, api_conf)
require_oauth = oauth_util.gen_resource_protector(D_TAG)

policy_fields = {
    'type': fields.String(example="p", enum=["p", "g"], required=True),
    # p: add a user/role,
    # g: make 'child' belong to 'father'
    'child': fields.String(example="ISNing"),
    'father': fields.String(example="GlobalAdmin"),
    'sub': fields.String(example="ISNing"),
    'obj': fields.String(example="books"),
    'act': fields.String(example="write"),
    'eft': fields.String(example="allow", enum=["allow", "deny"])
}

policy_model = api.model("policy", policy_fields)
policy_payload_fields = {"data": fields.Nested(policy_model)}
policy_payload_model = api.model("policy_payload", policy_payload_fields)
policies_list_payload_fields = {"data": fields.List(fields.Nested(policy_model), required=True)}
policies_list_payload_model = api.model("policies_list_payload", policies_list_payload_fields)

policy_ep_errs = {"get": []}


def init_app(_app):
    casbin.init_app(_app)


def first_run():
    load_default_policy()


def load_default_policy():
    perm_util.add_policy_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), './default.csv')))


@api.route('/policy', endpoint='policy_ep', methods=["POST", "DELETE"],
           doc={"get": {"responses": rest_util.gen_responses_doc(api, policy_ep_errs["get"])}})
class PolicyR(Resource):

    @api.expect(policy_payload_model)
    @api.response(200, "Success Response",
                  RestResponse({"added": True}, "success").get_model_registered(api, "policy_post_success_response"))
    @require_oauth(scopes["POLICIES_WRITE"])
    @require_permission(perms["POLICIES_WRITE"])
    def post(self):
        try:
            data = util.get_post_data().get("data")
        except AttributeError:
            raise InvalidJSONSyntaxException()
        try:
            if data['type'] == 'p':
                added = enforcer.add_policy(data['sub'], data['obj'], data['act'], data['eft'])
            elif data['type'] == 'g':
                added = enforcer.add_grouping_policy(data['child'], data['father'])
            else:
                raise InvalidJSONSyntaxException('\"type\" must be \"p\" or \"g\"')
        except KeyError:
            raise InvalidJSONSyntaxException()
        return RestResponse({"added": added}, "success")

    @api.expect(policy_payload_model)
    @api.response(200, "Success Response",
                  RestResponse(policy_model).get_model_registered(api, "policy_delete_success_response"))
    @require_oauth(scopes["POLICIES_WRITE"])
    @require_permission(perms["POLICIES_WRITE"])
    def delete(self):
        try:
            data = util.get_post_data().get("data")
        except AttributeError:
            raise InvalidJSONSyntaxException()
        try:
            if data['type'] == 'p':
                deleted = enforcer.remove_policy(data['sub'], data['obj'], data['act'], data['eft'])
            elif data['type'] == 'g':
                deleted = enforcer.remove_grouping_policy(data['child'], data['father'])
            else:
                raise InvalidJSONSyntaxException('\"type\" must be \"p\" or \"g\"')
        except KeyError:
            raise InvalidJSONSyntaxException()
        return RestResponse({"deleted": deleted}, "success")


permissions_ep_get_errs = []
permissions_domain_ep_get_errs = [DomainNotFoundException]
permissions_domain_name_ep_get_errs = [DomainNotFoundException, PermissionNotFoundException]


@api.route('/permissions', endpoint='permissions_ep',
           doc={"get": {"responses": rest_util.gen_responses_doc(api, permissions_ep_get_errs)}})
@api.route('/permissions/<domain>', endpoint='permissions_domain_ep',
           doc={"params": {'domain': "The permissions\' domain name"},
                "get": {"responses": rest_util.gen_responses_doc(api, permissions_domain_ep_get_errs)}})
@api.route('/permissions/<domain>/<name>', endpoint='permissions_domain_name_ep',
           doc={"params": {'domain': "The permission\'s domain name", 'name': "The permission\'s own name"},
                "get": {"responses": rest_util.gen_responses_doc(api, permissions_domain_name_ep_get_errs)}})
class PermissionsR(Resource):

    @api.response(200, "Success Response",
                  RestResponse(None).get_model_registered(api, "permissions_success_response"))
    @require_permission(perms["PERMISSIONS_READ"])
    @require_oauth(scopes["PERMISSIONS_READ"])
    def get(self, domain=None, name=None):
        all_permissions = enforcer.get_all_permissions_dict()
        if domain:
            domain_permissions = all_permissions.get(domain)
            if domain_permissions is None:
                raise DomainNotFoundException("Domain \"{}\" not found or not registered.".format(domain))
            if name:
                permission = domain_permissions.get(name)
                if permission is None:
                    raise PermissionNotFoundException(
                        "permission \"{0}.{1}\" not found or not registered.".format(domain, name))
                return RestResponse(permission)
            else:
                return RestResponse(domain_permissions)
        else:
            return RestResponse(all_permissions)
