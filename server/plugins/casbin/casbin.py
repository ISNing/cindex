import os

import casbin_sqlalchemy_adapter
from flask_sqlalchemy import SQLAlchemy

from App import util
from plugins.casbin.base_casbin import CEnforcer, Permission

default_conf = {
    'url_prefix': '/permissions',
    'model': '{work_dir}/casbin/model.conf'
}
conf = util.get_conf_checked('casbin', default_conf)


def write_in_default_model_conf(f):
    model_conf = util.read_file_content(os.path.abspath(os.path.join(os.path.dirname(__file__), "./model.conf")), None)
    f.write(model_conf)


db = None
adapter = None
model = CEnforcer.new_model(
    text=util.read_file_content(conf['model'].replace("{work_dir}", util.get_work_dir()), write_in_default_model_conf))
enforcer = CEnforcer(model, adapter)


def init_app(_app):
    global db, model, adapter, enforcer
    db = SQLAlchemy(_app)
    adapter = casbin_sqlalchemy_adapter.Adapter(db.engine)
    enforcer.set_adapter(adapter)


def register_permission(perm: Permission):
    """
    Register permission
    :param perm:A Permission object
    """
    enforcer.register_permission(perm)


def register_permissions(perms: list):
    """
    Register permissions in a list
    :param perms:A list of Permission objects
    """
    for perm in perms:
        register_permission(perm)
