from plugins.oauth import oauth_util
from plugins.oauth.oauth2 import register_scopes

D_TAG = "Drives"

scopes_conf = [
    {
        "nick": "FILES_READ",
        "name": "Files.Read",
        "description": ""
    },
    {
        "nick": "FILES_WRITE",
        "name": "Files.Write",
        "description": ""
    }
]

scopes = oauth_util.gen_scopes_from_conf(scopes_conf, domain=D_TAG)
register_scopes(scopes.values())
