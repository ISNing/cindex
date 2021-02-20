import json
import os
import time

from flask import Blueprint, request
from flask_restx import Resource, fields, marshal_with

from App import util, rest_util
from plugins.casbin import perm_util
from plugins.casbin.perm_util import require_permission
from plugins.oauth import oauth_util
from .api_config import api_conf
from .models import db, YellowPageData, Phone, Address, Website
from .oauth_config import scopes
from .perm_config import perms

default_conf = {
    'url_prefix': '/yellowpage/v1.0',
    'subdomain': 'api'
}
conf = util.get_conf_checked('exthmui.yellowpage.restful', default_conf)

module_name = 'exthmui_yellowpage'
impl = 'YellowPage'
description = 'A exthmui YellowPageData restful api blueprint module for flask.'
bp = yellowpage = Blueprint(module_name, module_name, url_prefix=conf['url_prefix'], subdomain=conf.get('subdomain'))
yellowpage_api = rest_util.gen_api(bp, api_conf)

D_TAG = "YellowPage"

require_oauth = oauth_util.gen_resource_protector(D_TAG)


def first_run():
    load_default_policy()


def load_default_policy():
    perm_util.add_policy_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), './default.csv')))


@yellowpage.before_app_first_request
def create_table():
    db.create_all()


item_fields = {
    'name': fields.String,
    'avatar': fields.String,
    'address': fields.List(fields.Nested({
        'data': fields.String,
        'label': fields.String
    })),
    'phone': fields.List(fields.Nested({
        'number': fields.String,
        'label': fields.String
    })),
    'website': fields.List(fields.Nested({
        'url': fields.String,
        'label': fields.String
    }))
}

yellowpage_list_fields = {
    'version': fields.Integer(default=int(time.time())),
    'status': fields.Integer,
    'data': fields.List(fields.Nested(item_fields))
}


class Item(object):
    def __init__(self, name, avatar, phone, address, website):
        self.name = name
        self.avatar = avatar
        self.phone = phone
        self.address = address
        self.website = website


class YellowPageList(object):
    def __init__(self, version, status, data):
        self.version = version
        self.status = status
        self.data = data


@marshal_with(item_fields)
def gen_item(name, avatar, phone, address, website):
    return Item(name, avatar, phone, address, website)


@marshal_with(item_fields)
def gen_item_by_data(data):
    return data


@marshal_with(yellowpage_list_fields)
def gen_items_list(version):
    result = {'data': db.session.query(YellowPageData).filter(YellowPageData.lastUpdated > version).all()}
    if result['data'] is None:
        result['status'] = 1
    return result


def get_item(name):
    return {
        'data': gen_item_by_data(YellowPageData.query.filter_by(name=name).first())
    }


def insert_data(i, version):
    ypdata = YellowPageData(name=i['name'], lastUpdated=version, avatar=i['avatar'])
    db.session.add(ypdata)
    for phone in i['phone']:
        p = Phone(number=phone['number'], label=phone['label'])
        ypdata.phone.append(p)
        db.session.add(p)
    for address in i['address']:
        a = Address(data=address['data'], label=address['label'])
        ypdata.address.append(a)
        db.session.add(a)
    for website in i['website']:
        w = Website(url=website['url'], label=website['label'])
        ypdata.website.append(w)
        db.session.add(w)
    db.session.commit()
    db.session.close()


def update_data(ypdata, i, version):
    phones = []
    addresses = []
    websites = []
    for phone in ypdata.phone:
        p = {'number': phone.number, 'label': phone.label}
        phones.append(p)
    for address in ypdata.address:
        a = {'data': address.data, 'label': address.label}
        addresses.append(a)
    for website in ypdata.website:
        a = {'url': website.url, 'label': website.label}
        websites.append(a)
    if ypdata.avatar == i['avatar'] and phones == i['phone'] and addresses == i['address'] and websites == i['website']:
        return False
    c = util.get_list_changed(phones, i['phone'])
    for d in c[0]:
        db.session.delete(Phone.query.filter_by(number=d['number'], masterid=ypdata.id).first())
    db.session.commit()
    for a in c[1]:
        t = Phone(number=a['number'], label=a['label'])
        db.session.add(t)
        ypdata.phone.append(t)
    c = util.get_list_changed(addresses, i['address'])
    for d in c[0]:
        db.session.delete(Address.query.filter_by(data=d['data'], masterid=ypdata.id).first())
    db.session.commit()
    for a in c[1]:
        t = Address(data=a['data'], label=a['label'])
        db.session.add(t)
        ypdata.address.append(t)
    c = util.get_list_changed(websites, i['address'])
    for d in c[0]:
        db.session.delete(Website.query.filter_by(url=d['url'], masterid=ypdata.id).first())
    db.session.commit()
    for a in c[1]:
        t = Website(url=a['url'], label=a['label'])
        db.session.add(t)
        ypdata.website.append(t)
    ypdata.lastUpdated = version
    ypdata.avatar = i['avatar']
    db.session.commit()
    db.session.close()
    return True


class DataListR(Resource):
    @require_oauth(scopes["DATA_WRITE"])
    @require_permission(perms["DATA_WRITE"])
    def post(self):
        data = json.loads(request.get_data(as_text=True))

        for item in data['data']:
            i = gen_item(item['name'], item['avatar'], item['phone'], item['address'], item['website'])
            ypdata = YellowPageData.query.filter_by(name=i['name']).first()
            if ypdata is None:
                insert_data(i, data['version'])
                continue
            if not update_data(ypdata, i, data['version']):
                continue
        return {'message': 'success'}, 200

    @staticmethod
    @require_oauth(scopes["DATA_READ"])
    @require_permission(perms["DATA_READ"])
    def get():
        version = request.args.get("version")
        res = gen_items_list(version if version is not None else 0)
        return res, 200 if res['status'] == 0 else 404 if res['status'] == 1 else 500


class DataR(Resource):
    @require_oauth(scopes["DATA_WRITE"])
    @require_permission(perms["DATA_WRITE"])
    def post(self, name):
        data = json.loads(request.get_data(as_text=True))

        item = data['data']
        i = gen_item(item['name'], item['avatar'], item['phone'], item['address'], item['website'])
        ypdata = YellowPageData.query.filter_by(name=name).first()
        if ypdata is None:
            insert_data(i, data['version'])
        if not update_data(ypdata, i, data['version']):
            pass
        return {'message': 'success'}, 200

    @staticmethod
    @require_oauth(scopes["DATA_WRITE"])
    @require_permission(perms["DATA_WRITE"])
    def delete(name):
        auth = request.headers.get('Authorization')
        if auth != 'deac987a-21c8-40c7-bedc-27bb30756fad':
            return {'message': 'authenticate failed'}, 401
        ypdata = YellowPageData.query.filter_by(name=name).first()
        if ypdata is None:
            return {
                       'data': 'Not found'
                   }, 404
        db.session.delete(ypdata)
        return {'data': 'success'}, 200

    @staticmethod
    @require_oauth(scopes["DATA_READ"])
    @require_permission(perms["DATA_READ"])
    def get(name):
        res = get_item(name)
        return res, 200


yellowpage_api.add_resource(DataListR, "/data")
yellowpage_api.add_resource(DataR, "/data/<name>")
