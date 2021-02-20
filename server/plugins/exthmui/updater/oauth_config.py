from plugins.oauth import oauth_util
from plugins.oauth.oauth2 import register_scopes

D_TAG = "Updater"

scopes_conf = [
    {
        "nick": "UPDATES_WRITE",
        "name": "Updates.Write",
        "description": ""
    },
    {
        "nick": "UPDATES_READ",
        "name": "Updates.Read",
        "description": ""
    },
    # {
    #     "nick": "CHANGES_RWA",
    #     "name": "Changes.ReadWriteAll",
    #     "description": ""
    # }
]

scopes = oauth_util.gen_scopes_from_conf(scopes_conf, domain=D_TAG)
register_scopes(scopes.values())
