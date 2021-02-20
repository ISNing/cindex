from authlib.integrations.flask_oauth2 import ResourceProtector, AuthorizationServer
from authlib.oauth2.rfc6750 import BearerTokenValidator

from plugins.oauth.models import OAuth2Token


class CResourceProtector(ResourceProtector):
    def __call__(self, ori_scope=None, operator: str = 'AND', optional: bool = False, domain: str = None):
        def get_scopes_names(o):
            if isinstance(o, str):
                return o.split(","), True
            elif isinstance(o, Scope):
                return [o.id], False
            else:
                raise TypeError("scopes must be list, str or Scope obj")

        if ori_scope is tuple or ori_scope is list:
            p1_scope = []
            for s in ori_scope:
                p1_scope.extend(get_scopes_names(s))
        else:
            p1_scope = get_scopes_names(ori_scope)
        if domain is not None:
            p2_scope = []
            if p1_scope[1]:
                for s in p1_scope[0]:
                    p2_scope.append("{0}.{1}".format(domain, s))
            else:
                p2_scope.extend(p1_scope[0])
        else:
            p2_scope = ori_scope
        return super().__call__(p2_scope, operator, optional)


class CAuthorizationServer(AuthorizationServer):
    scopes = {"Global": {}}

    def register_scope(self, scope):
        """
        Register scope object to server
        :param scope: The scope object expected to be registered
        """
        if not self.scopes.get(scope.domain):
            self.scopes[scope.domain] = {}
        self.scopes[scope.domain][scope.name] = scope

    def get_all_scopes(self):
        """
        Get all scopes registered
        :return: scopes registered
        """
        return self.scopes

    def get_all_scopes_dict(self):
        """
        Get all scopes registered
        :return: scopes registered
        """
        scopes_dict = {}
        for domain in self.scopes.keys():
            scopes_dict[domain] = {}
            for scope in self.scopes[domain].values():
                scopes_dict[domain][scope.name] = scope.__dict__()
        return scopes_dict


class Scope:
    def __init__(self, name, description, domain="Global"):
        self.name = name
        self.description = description
        self.domain = domain

    @property
    def id(self):
        if self.domain is not None:
            return "{0}.{1}".format(self.domain, self.name)
        else:
            return self.name

    def __dict__(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "domain": self.domain
        }


class CBearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        return OAuth2Token.query.filter_by(access_token=token_string).first()

    def request_invalid(self, request):
        return False

    def token_revoked(self, token):
        return token.revoked
