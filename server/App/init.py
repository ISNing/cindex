import importlib
import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import App.impls as impls
from App import util
from App.errors import MultipleImplementException, NotFullyImplementedException, NotModuleException
from App.impls import Module

conf = {}
impl_loaded = {}
db = SQLAlchemy()


def init_first_run():
    for module in impl_loaded.values():
        if hasattr(module, "first_run"):
            module.first_run()


def load_conf(app):
    global conf
    global impl_loaded
    conf = util.get_global_conf()
    imports = conf['configuration']['blu_imports']
    for i in imports:
        # noinspection PyTypeChecker
        module: Module = importlib.import_module('plugins.{}'.format(i))
        if False in map(lambda item: (item.startswith('_') or
                                      item in dir(module) and
                                      isinstance(getattr(module, item), type(getattr(Module(''), item)))),
                        dir(Module(''))):
            raise NotModuleException()
        if module.impl in dir(impls):
            Impl: Module = getattr(impls, module.impl)
            if False in map(lambda item: str(item.startswith('_') or
                                             item in dir(module) and
                                             isinstance(getattr(module, item), type(getattr(Impl(''), item)))),
                            dir(Impl(''))):
                raise NotFullyImplementedException()
        if impl_loaded.get(module.impl):
            raise MultipleImplementException()
        impl_loaded[module.impl] = module
        if hasattr(module, "init_app"):
            module.init_app(app)
        app.register_blueprint(module.bp)
        print('{0} has imported: {1} which implemented \'{2}\''.format(module.module_name, module.description,
                                                                       module.impl))


def create_app(config=None):
    app = Flask(__name__)

    # load default configuration
    app.config.update(util.get_global_conf()['configuration'].get('flask_config'))

    app.config['SERVER_NAME'] = util.get_global_conf()['configuration'].get('server_name')
    app.config['SECRET_KEY'] = util.get_global_conf()['configuration']['secret_key']

    database_uri = util.get_database_uri()
    database_uri = database_uri if database_uri else 'sqlite:///../{work_dir}/db.sqlite'
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # load environment configuration
    if 'WEBSITE_CONF' in os.environ:
        app.config.from_envvar('WEBSITE_CONF')

    # load App specified configuration
    if config is not None:
        if isinstance(config, dict):
            app.config.update(config)
        elif config.endswith('.py'):
            app.config.from_pyfile(config)

    setup_app(app)
    return app


def setup_app(app):
    db.init_app(app)
    load_conf(app)
