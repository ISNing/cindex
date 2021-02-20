from plugins.oauth.base_oauth import Scope, CResourceProtector, CBearerTokenValidator
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


def login(username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        raise UserNotFoundException()
    if not user.check_password(password):
        raise InvalidPasswordException()
    db.session['id'] = user.id
    return user


def signup(username, password, id=None):
    if User.query.filter_by(username=username).first():
        raise UserAlreadyExistsException()
    user = User(username=username, password=password)
    if id:
        user.id = id
    db.session.add(user)
    db.session.commit()
    return user
