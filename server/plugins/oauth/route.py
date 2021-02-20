import os
import time
import uuid
from abc import ABC

from authlib.oauth2 import OAuth2Error
from authlib.oidc.discovery.models import OpenIDProviderMetadata
from authlib.oidc.discovery.well_known import get_well_known_url
from flask import Blueprint, request, session, url_for, Flask
from flask import render_template, redirect
from flask.views import View
from werkzeug.security import gen_salt

from App import util
from plugins.casbin import perm_util
from . import oauth_util
from .models import db, User, OAuth2Client
from .oauth2 import authorization, config_oauth, RevocationEndpoint
from .restful import setup_api
# TODO:Remove it before production
from ..casbin.casbin import enforcer

os.environ['AUTHLIB_INSECURE_TRANSPORT'] = "true"
default_conf = {
    'url_prefix': '/login',
    'expired_in': 6000,
    'issuer': 'https://example.cn',
    'pub_key_path': 'oauth/public_key.pem',
    'priv_key_path': 'oauth/private_key.pem'
}
conf = util.get_conf_checked('oauth', default_conf)

impl = "oauth"
module_name = 'oauth'
description = 'A OAuth2 auth server blueprint module for flask.'
oidc = bp = Blueprint(module_name, module_name, url_prefix=conf['url_prefix'],
                      template_folder=os.path.dirname(__file__) + "/templates",
                      static_folder=os.path.dirname(__file__) + "/static", static_url_path="/")

config_oauth(Flask(__name__))


def first_run():
    add_root_user()
    load_default_policy()


def load_default_policy():
    perm_util.add_policy_from_csv(os.path.abspath(os.path.join(os.path.dirname(__file__), './default.csv')))


def add_root_user():
    passwd = str(uuid.uuid1())
    user = oauth_util.signup("root", passwd, id=0)
    print("Password for root user:{}".format(passwd))
    enforcer.add_grouping_policy(str(user.get_user_id()), 'roots')


def current_user():
    if 'id' in session:
        uid = session['id']
        return User.query.get(uid)
    return None


@bp.before_app_first_request
def create_table():
    db.create_all()


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


@bp.route(get_well_known_url('/'), methods=('GET',))
def well_known():
    return OpenIDProviderMetadata.we


@bp.route('/', methods=('GET', 'POST'))
def home():
    user = current_user()
    if not user:
        return redirect('login?next={}'.format(request.url))
    if user:
        clients = OAuth2Client.query.filter_by(user_id=user.id).all()
    else:
        clients = []

    return render_template('home.html', clients=clients)


@bp.route('/logout')
def logout():
    del session['id']
    next_page = request.args.get('next')
    return render_template('logout.html', next_page=next_page)


@bp.route('/create_client', methods=('GET', 'POST'))
def create_client():
    user = current_user()
    if not user:
        return redirect('')
    if request.method == 'GET':
        return render_template('create_client.html')

    client_id = gen_salt(24)
    client_id_issued_at = int(time.time())
    # noinspection PyArgumentList,PyArgumentList,PyArgumentList
    client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=user.id,
    )

    if client.token_endpoint_auth_method == 'none':
        client.client_secret = ''
    else:
        client.client_secret = gen_salt(48)

    form = request.form
    client_metadata = {
        "client_name": form["client_name"],
        "client_uri": form["client_uri"],
        "grant_types": split_by_crlf(form["grant_type"]),
        "redirect_uris": split_by_crlf(form["redirect_uri"]),
        "response_types": split_by_crlf(form["response_type"]),
        "scope": form["scope"],
        "token_endpoint_auth_method": form["token_endpoint_auth_method"]
    }
    client.set_client_metadata(client_metadata)
    db.session.add(client)
    db.session.commit()
    return redirect('/')


@bp.route('/oauth/authorize', methods=['GET', 'POST'])
def authorize():
    user = current_user()
    # if user log status is not true (Auth server), then to log it in
    if not user:
        return redirect(url_for('oauth.login_page', next=request.url))
    if request.method == 'GET':
        try:
            grant = authorization.validate_consent_request(end_user=user)
        except OAuth2Error as error:
            return error.error
        return render_template('authorize.html', user=user, grant=grant)
    if not user and 'username' in request.form:
        username = request.form.get('username')
        user = User.query.filter_by(username=username).first()
    if request.form['confirm']:
        grant_user = user
    else:
        grant_user = None
    return authorization.create_authorization_response(grant_user=grant_user)


@bp.route('/oauth/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@bp.route('/oauth/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response(RevocationEndpoint.ENDPOINT_NAME)


# TODO: Implement it: https://docs.authlib.org/en/v0.15.3/specs/rfc7662.html#register-introspection-endpoint
@bp.route('/oauth/introspect', methods=['POST'])
def introspect_token():
    raise NotImplementedError()
    # return authorization.create_endpoint_response(IntrospectionEndpoint.ENDPOINT_NAME)


class LoginV(View, ABC):

    def dispatch_request(self):
        if request.method == 'GET':
            user = current_user()
            next_page = request.args.get('next')
            return render_template("login.html", user=user, next_page=next_page)


class SignUpV(View, ABC):

    def dispatch_request(self):
        if request.method == 'GET':
            user = current_user()
            next_page = request.args.get('next')
            return render_template("signup.html", user=user, next_page=next_page)


bp.add_url_rule('/login', view_func=LoginV.as_view("login_page"))
bp.add_url_rule('/signup', view_func=SignUpV.as_view("signup_page"))

setup_api(bp)
