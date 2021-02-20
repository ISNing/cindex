import time
import urllib.parse

import requests
from flask import redirect
from flask_restx import marshal
from furl import furl

from App import util
from plugins.cloud_drive.base_drive import ItemSchema, Drive as _Drive, conf as cd_conf
from plugins.cloud_drive.base_drive import item_fields
from plugins.cloud_drive.errors import InvalidResourceURIException, UpstreamAPIError

default_conf = {
    'base_url': 'https://graph.microsoft.com/v1.0/',
    'client_id': '893a70dd-4a1e-4925-9b86-45903628aef4',
    'client_secret': '5UshT_Y0D8___OT-vu~j8K0fyt1tkXX~l2',
    'redirect_uri_register': 'https://isning.github.io/Oneindex-Redirect/',
    'redirect_uri_final': '{url_host}/{url_prefix}/{drive_id}/authorized',
    'scopes': 'offline_access files.readwrite.all',
    'select': "id,name,size,folder,image,video,lastModifiedDateTime,createdDateTime,createdBy,lastModifiedBy,"
              "@microsoft.graph.downloadUrl"
}
conf_pkg = 'drivers.one_drive'
conf = util.get_conf_checked(conf_pkg, default_conf)


def write_in_conf():
    util.set_part_conf_str(conf_pkg, conf)


class Drive(_Drive):
    base_url = conf['base_url']
    client_id = conf['client_id']
    client_secret = conf['client_secret']
    scopes = conf['scopes']
    select = conf['select']
    redirect_uri_register = conf['redirect_uri_register']
    redirect_uri_final = conf['redirect_uri_final']

    def gen_item(self, ori_dic: dict):
        if "folder" in ori_dic:
            ori_dic["type"] = "folder"
            ori_dic["childCount"] = ori_dic["folder"]["childCount"]
        else:
            ori_dic["downloadUrl"] = ori_dic["@microsoft.graph.downloadUrl"]
            ori_dic['mimeType'] = ori_dic['file']['mimeType']
            if "image" in ori_dic:
                ori_dic["type"] = "image"
            elif "video" in ori_dic:
                ori_dic["type"] = "video"
            else:
                ori_dic["type"] = "base_file"
        ori_dic['path'] = ori_dic['parentReference']['path'] + '/' + ori_dic['name']
        ori_dic["driveId"] = self.id
        dic = marshal(ori_dic, item_fields[ori_dic["type"]], skip_none=True)
        item = ItemSchema().load(dic)
        return item

    def login(self, request):
        global_conf = util.get_global_conf()
        final = request.args.get("final")
        url_login = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize" \
                    "?client_id={0}&scope={1}&response_type=code&redirect_uri={2}&state={3}" \
            .format(self.client_id, urllib.parse.quote(self.scopes), self.redirect_uri_register,
                    '{}*{}'.format(self.redirect_uri_final.replace('{url_host}',
                                                                   global_conf['configuration']['url_host'].strip('/'))
                                   .replace('{url_prefix}', cd_conf['url_prefix'].strip('/'))
                                   .replace('{drive_id}', self.conf['id'].strip('/')), final))
        return redirect(url_login)

    def authorized(self, request):
        code = request.args.get("code")
        final = request.args.get("final")
        url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        form = "client_id={}&redirect_uri={}&client_secret={}&code={}&grant_type=authorization_code".format(
            self.client_id, self.redirect_uri_register, self.client_secret, code)
        token = requests.post(url, headers=headers, data=form).json()
        if token.get('error'):
            return {'error': token['error'], 'http_code': 500}
        token["time"] = time.time()
        path = "me/drive"
        url = self.base_url + path
        access_token = token["access_token"]
        headers = {
            "Authorization": "bearer {}".format(access_token),
            "Content-Type": "application/json"
        }
        me = requests.get(url, headers=headers).json()
        try:
            token["account"] = me["owner"]["user"]["email"]
        except KeyError:
            token["account"] = me["owner"]["user"]["displayName"]
        token["drive"] = me["id"]
        self.conf['token'] = token
        self.write_in_conf()
        return redirect(final)

    def before_request(self):
        time_now = time.time()
        time_last = self.conf['token']['time']
        if time_now - time_last > self.conf['token']['expires_in'] - 60:
            url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri_register,
                "refresh_token": self.conf['token']['refresh_token'],
                "grant_type": "refresh_token",
                "scope": self.conf['token']['scope'],
            }
            try:
                data = requests.post(url, data=data, headers=headers).json()
            except requests.exceptions.ConnectionError:
                raise UpstreamAPIError()
            data['time'] = time.time()
            data['account'] = self.conf['token']['account']
            data['drive'] = self.conf['token']['drive']
            self.conf['token'] = data
            self.write_in_conf()

    def get_item_list(self, uri):
        """
        Get file list

        :return: File list <dict>
        """
        drive = self.conf['token']['drive']
        access_token = self.conf['token']["access_token"]
        headers = {
            "Authorization": "bearer {}".format(access_token),
            "Content-Type": "application/json"
        }
        url = gen_folder_children_ep_url(self.base_url, drive, uri)
        # TODO: Add select and item_per_page parameter
        # url = "{}?$top={}&$select={}".format(url, self.conf['items_per_page'], self.select)
        try:
            req = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            raise UpstreamAPIError()
        req_data = req.json()
        gen_err_from_od_if_found(req)
        item_list = req_data["value"]
        marshaled_list = []
        for i in item_list:
            marshaled_list.append(self.gen_item(i))
        # if "@odata.nextLink" in req_data:
        #     response["next"] = req_data["@odata.nextLink"]
        # else:
        #     response["next"] = None
        return marshaled_list

    def get_item(self, uri: str):
        """
        Get item by item id or path from device root

        :param uri: Allowed to be start with "id:" for get url by id, "path:" for get url by path from device root.
        :return: The information of the file requested
        """
        access_token = self.conf['token']["access_token"]
        headers = {
            "Authorization": "bearer {}".format(access_token),
            "Content-Type": "application/json"
        }
        drive = self.conf['token']["drive"]
        url = gen_item_ep_url(self.base_url, drive, uri)
        # TODO: Add right select parameter
        # url = "{}?$select={}".format(url, self.select)
        try:
            req = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            raise UpstreamAPIError()
        gen_err_from_od_if_found(req)
        req_data = req.json()
        return self.gen_item(req_data)

    def delete_item(self, uri: str):
        """
        Delete item by item id

        :param uri: Allowed to be start with "id:" for get url by id
        :return: The information of the file requested
       """
        access_token = self.conf['token']["access_token"]
        headers = {
            "Authorization": "bearer {}".format(access_token),
            "Content-Type": "application/json"
        }
        drive = self.conf['token']["drive"]
        url = gen_item_ep_url(self.base_url, drive, uri)
        try:
            req = requests.get(url, headers=headers)
        except requests.exceptions.ConnectionError:
            raise UpstreamAPIError()
        gen_err_from_od_if_found(req)
        return req.status_code


def gen_item_ep_url(base_url, drive, uri):
    uri = furl(uri)
    segments = uri.path.segments.copy()
    locator = segments.pop(0)
    location = ''.join(str(i) for i in segments)
    if locator == 'id:':
        path = 'drives/{}/items/{}'.format(drive, location)
    elif locator == 'path:':
        if location == '':
            path = 'drives/{}/root'.format(drive, location)
        else:
            path = 'drives/{}/root:/{}'.format(drive, location)
    else:
        raise InvalidResourceURIException('Key must be start with "id:" or "path:"')
    return base_url + path


def gen_folder_children_ep_url(base_url, drive, uri):
    uri = furl(uri)
    segments = uri.path.segments.copy()
    locator = segments.pop(0)
    item_url = gen_item_ep_url(base_url, drive, uri)
    location = ''.join(str(i) for i in segments)
    if locator == 'id:':
        return "{}/children".format(item_url)
    elif location == '':
        return "{}/children".format(item_url)
    else:
        return "{}:/children".format(item_url)


def gen_err_from_od_if_found(req):
    # noinspection PyBroadException
    try:
        if req.json().get('error'):
            e = UpstreamAPIError(req.json()['error']['message'])
            e.code = req.json()['error']['code']
            e.status_code = req.status_code
            raise e
    except UpstreamAPIError as ex:
        raise ex
    except Exception as ex:
        raise UpstreamAPIError(ex)
