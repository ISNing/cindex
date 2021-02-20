from plugins.casbin import perm_util
from plugins.casbin.casbin import register_permissions
from plugins.casbin.oauth_config import D_TAG

peerms_conf = [
]

perms = perm_util.gen_perms_from_conf(peerms_conf, domain=D_TAG)
register_permissions(perms.values())
