from plugins.oauth import oauth_util
from plugins.oauth.oauth2 import register_scopes

D_TAG = "Openid"

scopes_conf = [
]

scopes = oauth_util.gen_scopes_from_conf(scopes_conf, domain=D_TAG)
register_scopes(scopes.values())
