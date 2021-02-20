import importlib
import logging

from authlib.integrations.flask_oauth2 import current_token
from flask_restx import marshal, fields
from furl import furl

from App import util
from App.base_restful import RestResponse
from plugins.casbin.casbin import enforcer
from plugins.casbin.errors import NoPermissionAccessException
from plugins.cloud_drive.base_drive import DriveConf, item_fields, drive_conf_fields, conf_pkg, conf
from plugins.cloud_drive.errors import InvalidDriveConfException, DriveNotFoundException, InvalidResourceURIException

logger = logging.getLogger(__name__)

drives = {}
drivers = {}


def write_in_conf(_conf_pkg=conf_pkg, _conf=conf):
    util.set_part_conf_str(_conf_pkg, _conf)


def import_drive(drive_conf: dict, id: str):
    global drives, drivers
    pkg = 'package name get failed'
    try:
        pkg = '.drivers.' + drive_conf['driver']['pkg']
        driver = importlib.import_module(pkg, package='plugins.cloud_drive')
        drivers[driver.__name__] = driver
        # noinspection PyUnresolvedReferences
        drives[drive_conf['id']] = driver.Drive(drive_conf, id)
    except ModuleNotFoundError:
        logger.error('Module of driver \'{}\' not found, ignoring...'.format(pkg))


def import_drives(confs: dict):
    for drive_id in confs.keys():
        import_drive(confs[drive_id], drive_id)


def new_drive(drive_conf: dict, _conf=conf):
    conf_bak = _conf['drives'].copy()

    def reset_to_bak():
        _conf['drives'] = conf_bak
        import_drives(_conf['drives'])

    try:
        if drive_conf['id'] == 'new':
            reset_to_bak()
            raise InvalidDriveConfException('Making drive\'s id \"new\" is not allowed')
        drive_conf = marshal(
            DriveConf(drive_conf['id'], drive_conf['driver']),
            drive_conf_fields)
        _conf['drives'][drive_conf['id']] = drive_conf
        import_drives(_conf['drives'])
        write_in_conf(conf_pkg, _conf)
        return RestResponse(None, "success")
    except KeyError as ex:
        raise InvalidDriveConfException()


def get_drive(drive_id: str, _drives=None):
    if _drives is None:
        _drives = drives
    try:
        return _drives[drive_id]
    except KeyError:
        raise DriveNotFoundException()


def gen_uri_by_key(drive_id, key):
    uri = 'drives://{host}/{key}'.format(host=drive_id, key=key)
    return uri


def marshal_selects(data, selects):
    temp_fields = None
    if selects is not None:
        selects = selects.split(',')
        temp_fields = {}
        for select in selects:
            temp_fields[select] = fields.Raw
    if temp_fields:
        data = marshal(data, temp_fields, skip_none=True)
    return marshal(data, item_fields[data["type"]], skip_none=True)


def enforce_item(uri):
    if not enforcer.cenforce(uri):
        if not current_token:
            username = "anonymous"
            uid = "anonymous"
        else:
            username = current_token.user.username
            uid = current_token.user.get_user_id()
        raise NoPermissionAccessException(
            "User {0} uid {1} has no permission accessing this resource".format(username, uid))


def get_item_by_uri(uri):
    uri = furl(uri)
    if uri.scheme != 'drives':
        raise InvalidResourceURIException("Only \"drives\" scheme is allowed")
    drive = get_drive(uri.host)
    drive.before_request()
    return drive.get_item(uri)


def get_item_list_by_uri(uri):
    uri = furl(uri)
    if uri.scheme != 'drives':
        raise InvalidResourceURIException("Only \"drives\" scheme is allowed")
    drive = get_drive(uri.host)
    drive.before_request()
    return drive.get_item_list(uri)


def get_dl_url_by_uri(uri):
    item = get_item_by_uri(uri)
    return item.downloadUrl
