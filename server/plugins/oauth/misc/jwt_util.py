from datetime import datetime, timedelta

import jwt

from App import util


def generate_access_token(key, uid: str, algorithm: str, issuer: str, exp: int):
    now = datetime.utcnow()
    exp_datetime = now + timedelta(seconds=exp)
    access_payload = {
        'exp': exp_datetime,
        'iat': now,  # 开始时间
        'iss': issuer,  # 签名
        'data': {
            'flag': 0,  # 标识是否为一次性token，0是，1不是
            'uid': uid  # 用户名(自定义部分)
        }
    }
    access_token = jwt.encode(access_payload, key, algorithm=algorithm)
    return access_token


def decode_auth_token(key, token: str, algorithms):
    try:
        payload = jwt.decode(token, key=key, algorithms=algorithms)
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, jwt.InvalidSignatureError):
        return ""
    else:
        return payload


def identify(key, token: str):
    """
    用户鉴权
    """

    if token:
        payload = decode_auth_token(key, token)
        if not payload:
            return False
        if "uid" in payload and "flag" in payload:
            if payload["flag"] == 0:
                return payload["uid"]
            else:
                return False
    return False
