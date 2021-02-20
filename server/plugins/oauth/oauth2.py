from abc import ABC

from authlib.integrations.sqla_oauth2 import (
    create_query_client_func,
    create_save_token_func,
    create_bearer_token_validator,
)
from authlib.oauth2.rfc6749.grants import (
    AuthorizationCodeGrant as _AuthorizationCodeGrant,
    ResourceOwnerPasswordCredentialsGrant as _PasswordGrant,
    ClientCredentialsGrant as _ClientCredentialsGrant
)
from authlib.oauth2.rfc7009 import RevocationEndpoint as _RevocationEndpoint
from authlib.oidc.core import UserInfo
from authlib.oidc.core.grants import (
    OpenIDCode as _OpenIDCode,
    OpenIDImplicitGrant as _OpenIDImplicitGrant,
    OpenIDHybridGrant as _OpenIDHybridGrant,
)

from App import util
from .base_oauth import CResourceProtector, CAuthorizationServer, Scope
from .models import OAuth2Client, OAuth2AuthorizationCode, OAuth2Token
from .models import db, User

global_conf = util.get_global_conf()
conf = util.get_conf('oauth')

pub_key_path = 'oauth/public_key.pem'
priv_key_path = 'oauth/private_key.pem'
if conf["pub_key_path"] and conf["priv_key_path"]:
    pub_key_path = conf["pub_key_path"]
    priv_key_path = conf["priv_key_path"]
pub_key_path = util.get_path_relate_from_work_dir(pub_key_path)
priv_key_path = util.get_path_relate_from_work_dir(priv_key_path)

key = util.get_keys(pub_key_path, priv_key_path)

DUMMY_JWT_CONFIG = {
    'key': key,
    'alg': 'RS256',
    'iss': conf['issuer'],
    'exp': conf['expired_in'],
}


def exists_nonce(nonce, req):
    exists = OAuth2AuthorizationCode.query.filter_by(
        client_id=req.client_id, nonce=nonce
    ).first()
    return bool(exists)


# noinspection PyUnusedLocal
def generate_user_info(user, scope):
    return UserInfo(sub=str(user.id), name=user.username)


# -- Grants -- #

class AuthorizationCodeGrant(_AuthorizationCodeGrant, ABC):
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic', 'client_secret_post', 'none']

    def save_authorization_code(self, code, request):
        client = request.client
        # noinspection PyArgumentList,PyArgumentList,PyArgumentList,PyArgumentList,PyArgumentList
        auth_code = OAuth2AuthorizationCode(
            code=code,
            client_id=client.client_id,
            redirect_uri=request.redirect_uri,
            scope=request.scope,
            user_id=request.user.id,
        )
        db.session.add(auth_code)
        db.session.commit()
        return auth_code

    @staticmethod
    def query_authorization_code(code, client):
        item = OAuth2AuthorizationCode.query.filter_by(
            code=code, client_id=client.client_id).first()
        if item and not item.is_expired():
            return item

    def delete_authorization_code(self, authorization_code):
        db.session.delete(authorization_code)
        db.session.commit()

    def authenticate_user(self, authorization_code):
        return User.query.get(authorization_code.user_id)


class OpenIDCode(_OpenIDCode):
    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def get_jwt_config(self, grant):
        return DUMMY_JWT_CONFIG

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)


class ImplicitGrant(_OpenIDImplicitGrant):
    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def get_jwt_config(self):
        return DUMMY_JWT_CONFIG

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)


class PasswordGrant(_PasswordGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic']

    def authenticate_user(self, username, password):
        user = User.query.filter_by(username=username).first()
        if user.check_password(password):
            return user


class ClientCredentialsGrant(_ClientCredentialsGrant):
    TOKEN_ENDPOINT_AUTH_METHODS = ['client_secret_basic']


class HybridGrant(_OpenIDHybridGrant):
    def save_authorization_code(self, code, request):
        pass

    def exists_nonce(self, nonce, request):
        return exists_nonce(nonce, request)

    def get_jwt_config(self):
        return DUMMY_JWT_CONFIG

    def generate_user_info(self, user, scope):
        return generate_user_info(user, scope)


# -- Endpoints -- #


class RevocationEndpoint(_RevocationEndpoint):
    def query_token(self, token, token_type_hint, client):
        q = OAuth2Token.query.filter_by(client_id=client.client_id)
        if token_type_hint == 'access_token':
            return q.filter_by(access_token=token).first()
        elif token_type_hint == 'refresh_token':
            return q.filter_by(refresh_token=token).first()
        # without token_type_hint
        item = q.filter_by(access_token=token).first()
        if item:
            return item
        return q.filter_by(refresh_token=token).first()

    @staticmethod
    def revoke_token(token):
        token.revoked = True
        db.session.add(token)
        db.session.commit()


# TODO: Implement it: https://docs.authlib.org/en/v0.15.3/specs/rfc7662.html#register-introspection-endpoint
# class MyIntrospectionEndpoint(IntrospectionEndpoint):
#     def query_token(self, token, token_type_hint, client):
#         if token_type_hint == 'access_token':
#             tok = Token.query.filter_by(access_token=token).first()
#         elif token_type_hint == 'refresh_token':
#             tok = Token.query.filter_by(refresh_token=token).first()
#         else:
#             # without token_type_hint
#             tok = Token.query.filter_by(access_token=token).first()
#             if not tok:
#                 tok = Token.query.filter_by(refresh_token=token).first()
#         if tok:
#             if tok.client_id == client.client_id:
#                 return tok
#             if has_introspect_permission(client):
#                 return tok
#
#     def introspect_token(self, token):
#         return {
#             'active': True,
#             'client_id': token.client_id,
#             'token_type': token.token_type,
#             'username': get_token_username(token),
#             'scope': token.get_scope(),
#             'sub': get_token_user_sub(token),
#             'aud': token.client_id,
#             'iss': 'https://server.example.com/',
#             'exp': token.expires_at,
#             'iat': token.issued_at,
#         }


authorization = CAuthorizationServer()
require_oauth = CResourceProtector()


def register_scope(scope: Scope):
    """
    Register scope
    :param scope:A Scope object
    """
    authorization.register_scope(scope)


def register_scopes(scopes: list):
    """
    Register scopes in a list
    :param scopes:A list of Scope objects
    """
    for scope in scopes:
        register_scope(scope)


def config_oauth(app):
    query_client = create_query_client_func(db.session, OAuth2Client)
    save_token = create_save_token_func(db.session, OAuth2Token)
    authorization.init_app(
        app,
        query_client=query_client,
        save_token=save_token
    )

    # support all openid grants
    authorization.register_grant(AuthorizationCodeGrant, [
        OpenIDCode(require_nonce=True),
    ])
    authorization.register_grant(ImplicitGrant)
    # authorization.register_grant(PasswordGrant)
    # authorization.register_grant(ClientCredentialsGrant)
    authorization.register_grant(HybridGrant)

    # register endpoints
    authorization.register_endpoint(RevocationEndpoint)
    # authorization.register_endpoint(IntrospectionEndpoint)

    # protect resource
    bearer_cls = create_bearer_token_validator(db.session, OAuth2Token)
    require_oauth.register_token_validator(bearer_cls())
