from authlib.integrations.flask_oauth2 import current_token
from casbin import Enforcer


class Permission:
    def __init__(self, obj, act, description, domain="Global"):
        self._obj = obj
        self.act = act
        self.description = description
        self.domain = domain

    @property
    def id(self):
        return "{0}_{1}".format(self.obj.upper(), self.act.upper())

    @property
    def obj(self):
        return "{0}:{1}".format(self.domain, self._obj)

    @obj.setter
    def obj(self, v):
        self._obj = v

    @property
    def name(self):
        return "{0}:{1}".format(self._obj, self.act)

    def __dict__(self):
        return {
            "obj": self.obj,
            "act": self.act,
            "description": self.description,
            "domain": self.domain
        }


class CEnforcer(Enforcer):
    permissions = {}

    def cenforce(self, _obj, act=None):
        if type(_obj) is Permission:
            obj = _obj.obj
            act = _obj.act
        else:
            obj = _obj
        if not current_token:
            uid = "anonymous"
        else:
            uid = current_token.user.get_user_id()
        return self.enforce(uid, obj, act)

    def register_permission(self, perm):
        """
        Register scope object to server
        :param perm: The scope object expected to be registered
        """
        if not self.permissions.get(perm.domain):
            self.permissions[perm.domain] = {}
        self.permissions[perm.domain][perm.name] = perm

    def get_all_permissions(self):
        """
        Get all scopes registered
        :return: scopes registered
        """
        return self.permissions

    def get_all_permissions_dict(self):
        """
        Get all scopes registered
        :return: scopes registered
        """
        permissions_dict = {}
        for domain in self.permissions.keys():
            permissions_dict[domain] = {}
            for perm in self.permissions[domain].values():
                permissions_dict[domain][perm.name] = perm.__dict__()
        return permissions_dict
