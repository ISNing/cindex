from plugins.oauth.base_oauth import Scope, CResourceProtector, CBearerTokenValidator
from plugins.oauth.errors import UserNotFoundException, InvalidPasswordException, UserAlreadyExistsException
from plugins.oauth.misc.jwt_util import generate_access_token
from plugins.oauth.models import User, db


def get_user(uid: str = None, username: str = None):
    user = None
    if uid:
        user = User.query.filter_by(id=uid).first()
    elif username:
        user = User.query.filter_by(username=username).first()
    return user


def identify_with_passwd(user: User, password: str):
    return user.check_password(password)


def get_id_token(key, uid: str, algorithm: str, issuer: str, exp: int):
    return generate_access_token(key, uid, algorithm, issuer, exp)


def signup(username, password, id=None):
    if User.query.filter_by(username=username).first():
        raise UserAlreadyExistsException()
    user = User(username=username, password=password)
    if id:
        user.id = id
    db.session.add(user)
    db.session.commit()
    return user
