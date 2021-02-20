import flask_restx as rest
from flask_marshmallow import Schema
from flask_marshmallow.fields import fields as ma_fields
from flask_restx import marshal, Model
from marshmallow import post_load

from App import util

default_conf = {
    'url_prefix': '/drives',
    'drives': {},
    'configuration': {
        'items_per_page': 50
    }
}
conf_pkg = 'cloud_drive.configuration'

conf = util.get_conf_checked(conf_pkg, default_conf)
models = []

operated_by_fields = {
    "email": rest.fields.String(example="ISNing@exthmui.cn"),
    "displayName": rest.fields.String(example="ISNing")
}

operated_by_model = Model("operated_by", operated_by_fields)
models.append(operated_by_model)

item_fields_base = {
    "type": rest.fields.String(),
    "downloadUrl": rest.fields.String(),
    "createdDateTime": rest.fields.DateTime(example="2020-10-17T22:15:49Z"),
    "id": rest.fields.String(example="01KWYWBHR27ZEMCXABLJB2TEIV2TUQVTQS"),
    "lastModifiedDateTime": rest.fields.String(example="2020-10-17T22:15:51Z"),
    "name": rest.fields.String(example="example.zip"),
    "webUrl": rest.fields.String(example="https://exthm-my.sharepoint.com/personal/cd1a_exthmui_cn/folder/example.zip"),
    "size": rest.fields.Integer(example=7098404),
    "driveId": rest.fields.String(example="cd1a"),
    "path": rest.fields.String(example="/folder/"),
    "createdBy": rest.fields.Nested(operated_by_model, skip_none=True),
    "lastModifiedBy": rest.fields.Nested(operated_by_model, skip_none=True),
    "mimeType": rest.fields.String(example="image/jpeg")
}
item_fields = {
    'base_file': item_fields_base.copy(),
    'folder': item_fields_base.copy(),
    'image': item_fields_base.copy(),
    'video': item_fields_base.copy()
}

item_fields['folder'].pop('downloadUrl')
item_fields['folder']['childCount'] = rest.fields.Integer(example=22)

item_model = Model("item", item_fields['base_file'])
models.append(item_model)

drive_conf_driver_fields = {
    'pkg': rest.fields.String(example='one_drive')
}

drive_conf_driver_model = Model("drive_conf_driver", drive_conf_driver_fields)
models.append(drive_conf_driver_model)

drive_conf_fields = {
    'id': rest.fields.String(example='drive-1'),
    'driver': rest.fields.Nested(drive_conf_driver_model),
    'items_per_page': rest.fields.Integer(example=conf['configuration']['items_per_page'])
}

drive_conf_model = Model("drive_conf", drive_conf_fields)
models.append(drive_conf_model)

drive_conf_payload_fields = {
    "data": rest.fields.Nested(drive_conf_model)
}

drive_conf_payload_model = Model("drive_conf_payload", drive_conf_payload_fields)
models.append(drive_conf_payload_model)


class DriveConf(object):
    def __init__(self, drive_id, driver):
        self.id = drive_id
        self.driver = marshal(DriveConfDriver(driver['pkg']), drive_conf_driver_fields)


class DriveConfDriver(object):
    def __init__(self, pkg):
        self.pkg = pkg


class Drive:
    id = None
    conf_base_pkg = 'cloud_drive.configuration.drives.{id}'

    @property
    def conf_pkg(self):
        return self.conf_base_pkg.format(id=self.id)

    def __init__(self, drive_conf: dict, id: str):
        self.conf = drive_conf
        self.id = id

    def before_request(self):
        raise NotImplementedError

    def write_in_conf(self):
        util.set_part_conf_str(self.conf_pkg, self.conf)

    def login(self, request):
        raise NotImplementedError

    def authorized(self, request):
        raise NotImplementedError

    def get_item_list(self, uri: str):
        """
        Get file list

        :return: File list <dict>
        """
        raise NotImplementedError

    def get_item(self, uri: str):
        """
        Get item by item id or path from device root

        :param uri: Allowed to be start with "id:" for get url by id, "path:" for get url by path from device root.
        :return: The information of the file requested
        """
        raise NotImplementedError

    def delete_item(self, uri: str):
        """
        Delete item by item id

        :param uri: Allowed to be start with "id:" for get url by id
        :return: The information of the file requested
        """
        raise NotImplementedError


class OperatedBySchema(Schema):
    email = ma_fields.Email()
    displayName = ma_fields.String()


class ItemSchema(Schema):
    childCount = ma_fields.Integer()
    type = ma_fields.String(required=True)
    downloadUrl = ma_fields.Url()
    createdDateTime = ma_fields.String(required=True)
    id = ma_fields.String(required=True)
    lastModifiedDateTime = ma_fields.String(required=True)
    name = ma_fields.String(required=True)
    webUrl = ma_fields.Url()
    size = ma_fields.Integer()
    driveId = ma_fields.String(required=True)
    path = ma_fields.String(required=True)
    createdBy = ma_fields.Nested(OperatedBySchema)
    lastModifiedBy = ma_fields.Nested(OperatedBySchema)
    mimeType = ma_fields.String()

    @post_load
    def make_user(self, data, many, **kwargs):
        if many:
            res = []
            for d in data:
                res.append(Item(**d))
        else:
            res = Item(**data)
        return res


class Item:
    def __init__(self, type, createdDateTime, id, lastModifiedDateTime, name, driveId, path, childCount=None,
                 downloadUrl=None, webUrl=None, size=None, createdBy=None, lastModifiedBy=None, mimeType=None):
        self.childCount = childCount
        self.type = type
        self.downloadUrl = downloadUrl
        self.createdDateTime = createdDateTime
        self.id = id
        self.lastModifiedDateTime = lastModifiedDateTime
        self.name = name
        self.webUrl = webUrl
        self.size = size
        self.driveId = driveId
        self.path = path
        self.createdBy = createdBy
        self.lastModifiedBy = lastModifiedBy
        self.mimeType = mimeType

    @property
    def uri_id(self):
        return 'drives://{0}/id:/{1}'.format(self.driveId, self.id)

    @property
    def uri_path(self):
        return 'drives://{0}/path:/{1}'.format(self.driveId, self.path)
