import functools

from authlib.integrations.flask_oauth2 import current_token

from App import util
from plugins.casbin.base_casbin import Permission
from plugins.casbin.casbin import enforcer
from plugins.casbin.errors import NoPermissionAccessException


def require_permission(_obj, act=None):
    def warpper(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            nonlocal _obj, act
            if not current_token:
                username = "anonymous"
                uid = "anonymous"
            else:
                username = current_token.user.username
                uid = current_token.user.get_user_id()
            if not enforcer.cenforce(uid, _obj, act):
                raise NoPermissionAccessException(
                    "User {0} uid {1} has no permission accessing this resource".format(username, uid))
            return f(*args, **kwargs)

        return decorated

    return warpper


def gen_perms_from_conf(scope_conf: list, domain=None):
    """
    Generate permission objects from conf like::

        [{
            "obj": "Policy",
            "act": "write",
            "description": ""
        },, ...]

    :param scope_conf: A config list
    :param domain: A string described what module is this scope belonged to,
        will be added to the start of obj as domain+":"+scope_name as obj of permission
    :return: A dict of Scope object, the Scope object's name are their name which is defined in the conf list.
        So, you can refer to them by *returned_dict.SCOPE_A*
    """
    permissions = {}
    if domain is not None:
        for s in scope_conf:
            p = Permission(obj=s["obj"], act=s["act"], description=s["description"], domain=domain)
            permissions[p.id.split(':', 1)[1]] = p
    else:
        for s in scope_conf:
            p = Permission(obj=s["obj"], act=s["act"], description=s["description"])
            permissions[p.id.split(':', 1)[1]] = p
    return permissions


def add_policy_from_csv(path):
    import csv
    c = csv.reader(util.read_file_content(path, None))
    for row in c:
        if len(row) < 2:
            continue
        if row.pop(0) == "p":
            enforcer.add_policy(*row)
        elif row.pop(0) == "g":
            enforcer.add_grouping_policy(*row)
        else:
            continue
