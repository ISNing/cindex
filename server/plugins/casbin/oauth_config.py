from plugins.oauth import oauth_util
from plugins.oauth.oauth2 import register_scopes

D_TAG = "Casbin"

scopes_conf = [
    {
        "nick": "POLICIES_WRITE",
        "name": "Policies.Write",
        "description": ""
    },
    {
        "nick": "POLICIES_READ",
        "name": "Policies.Read",
        "description": ""
    },
    {
        "nick": "PERMISSIONS_READ",
        "name": "Permissions.Read",
        "description": ""
    }
]

scopes = oauth_util.gen_scopes_from_conf(scopes_conf, domain=D_TAG)
register_scopes(scopes.values())
