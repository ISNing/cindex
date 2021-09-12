from App import util
from plugins.oauth.base_oauth import Scope, CResourceProtector, CBearerTokenValidator
from plugins.oauth.constants import default_conf
from plugins.oauth.errors import UserNotFoundException, InvalidPasswordException, UserAlreadyExistsException
from plugins.oauth.models import User, db


def gen_resource_protector(domain):
    def wrapper(scope, operator="AND", optional=False):
        require_oauth = CResourceProtector()
        require_oauth.register_token_validator(CBearerTokenValidator())
        return require_oauth(ori_scope=scope, operator=operator, optional=optional, domain=domain)

    return wrapper


def gen_scopes_from_conf(scope_conf: list, domain=None):
    """
    Generate scopes from conf like::

        [{
            "nick": "SCOPE_A"
            "name": "Scope.a"
            "description": "Some description for this scope..."
        }, ...]

    :param scope_conf: A config list
    :param domain: A string described what module is this scope belonged to, 
        will be added to the start of name as domain+"."+scope_name as id of scope
    :return: A dict of Scope object, the Scope object's name are their *nick* which is defined in the conf list.
        So, you can refer to them by *returned_dict.SCOPE_A*
    """
    scopes = {}
    if domain is not None:
        for s in scope_conf:
            scopes[s["nick"]] = Scope(name=s["name"], description=s["description"], domain=domain)
    else:
        for s in scope_conf:
            scopes[s["nick"]] = Scope(name=s["name"], description=s["description"])
    return scopes


def get_key_paths():
    get_conf = util.gen_get_conf_checked('oauth', default_conf)

    pub_key_path = 'oauth/public_key.pem'
    priv_key_path = 'oauth/private_key.pem'
    if get_conf("pub_key_path") and get_conf("priv_key_path"):
        pub_key_path = get_conf("pub_key_path")
        priv_key_path = get_conf("priv_key_path")
    pub_key_path = util.get_path_relate_from_work_dir(pub_key_path)
    priv_key_path = util.get_path_relate_from_work_dir(priv_key_path)
    return pub_key_path, priv_key_path
