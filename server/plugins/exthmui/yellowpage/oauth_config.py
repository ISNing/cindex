from plugins.oauth import oauth_util
from plugins.oauth.oauth2 import register_scopes

D_TAG = "YellowPage"

scopes_conf = [
    {
        "nick": "DATA_WRITE",
        "name": "Data.Write",
        "description": ""
    },
    {
        "nick": "DATA_READ",
        "name": "Data.Read",
        "description": ""
    }
]

scopes = oauth_util.gen_scopes_from_conf(scopes_conf, domain=D_TAG)
register_scopes(scopes.values())
