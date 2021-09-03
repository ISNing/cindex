from flask import Blueprint
from flask.globals import session
from flask_restx import Resource, fields

from App import util, rest_util
from App.base_restful import CApi, RestResponse
from . import oauth_util
from .api_config import api_conf
from .errors import UserNotFoundException, InvalidPasswordException, UserAlreadyExistsException, \
    InvalidOperationException, ScopeNotFoundException, DomainNotFoundException
from .oauth_config import D_TAG

require_oauth = oauth_util.gen_resource_protector(D_TAG)

uc_api: CApi = rest_util.gen_api(None, api_conf)
api: CApi = uc_api


def setup_api(bp: Blueprint):
    global uc_api, api
    # noinspection PyTypeChecker
    api.init_app(bp)


userC = api.model('users_expected_content', {
    'password': fields.String(description="The password of the user."),
    'operation': fields.String(description="The operation client want server do.", enum=["login", "signup"]),
})

user_ep_post_errs = [UserNotFoundException, InvalidPasswordException, UserAlreadyExistsException,
                     InvalidOperationException]


@api.route('/users/<username>', endpoint='user_ep', doc={"post": rest_util.gen_responses_doc(api, user_ep_post_errs)})
@api.doc(params={'username': "The user\'s username"})
class UserR(Resource):

    @api.expect(userC)
    @api.response(200, "Success Response",
                  RestResponse(None, "success").get_model_registered(api, "users_success_response"))
    def post(self, username):
        data = util.get_post_data()
        operation = data.get('operation')
        password = data.get('password')
        if operation == 'login':
            oauth_util.login(username, password, session)
            return RestResponse(None, "success")
        elif operation == 'signup':
            oauth_util.signup(username, password)
            return RestResponse(None, "success")
        else:
            raise InvalidOperationException()


management_scopes_ep_get_errs = []
management_scopes_domain_ep_get_errs = [DomainNotFoundException]
management_scopes_domain_name_ep_get_errs = [DomainNotFoundException, ScopeNotFoundException]


@api.route('/manage/scopes', endpoint='management_scopes_ep',
           doc={"get": {"responses": rest_util.gen_responses_doc(api, management_scopes_ep_get_errs)}})
@api.route('/manage/scopes/<domain>', endpoint='management_scopes_domain_ep',
           doc={"params": {'domain': "The scopes\' domain name"},
                "get": {"responses": rest_util.gen_responses_doc(api, management_scopes_domain_ep_get_errs)}})
@api.route('/manage/scopes/<domain>/<name>', endpoint='management_scopes_domain_name_ep',
           doc={"params": {'domain': "The scope\'s domain name", 'name': "The scope\'s own name"},
                "get": {"responses": rest_util.gen_responses_doc(api, management_scopes_domain_name_ep_get_errs)}})
class ScopesR(Resource):

    @api.response(200, "Success Response",
                  RestResponse(None).get_model_registered(api, "manage_scopes_success_response"))
    def get(self, domain=None, name=None):
        from plugins.oauth.oauth2 import authorization
        all_scopes = authorization.get_all_scopes_dict()
        if domain:
            domain_scopes = all_scopes.get(domain)
            if domain_scopes is None:
                raise DomainNotFoundException("Domain \"{}\" not found or not registered.".format(domain))
            if name:
                scope = domain_scopes.get(name)
                if scope is None:
                    raise ScopeNotFoundException(
                        "Scope \"{0}.{1}\" not found or not registered.".format(domain, name))
                return RestResponse(scope)
            else:
                return RestResponse(domain_scopes)
        else:
            return RestResponse(all_scopes)
