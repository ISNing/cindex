from types import ModuleType

from flask import Blueprint
from flask_sqlalchemy import Model


class Module(ModuleType):
    def __call__(self, *args, **kwargs):
        pass

    def __init__(self, name: str):
        super().__init__(name)
        self.impl: str = str()
        self.module_name: str = str()
        self.bp: Blueprint = Blueprint('', '')
        self.description: str = str()


class UserControlling(Module):
    def __call__(self, *args, **kwargs):
        pass

    def __init__(self, name: str):
        super().__init__(name)
        self.User: Model = Model()
        self.query_by_id = base_function
        self.auth_user = base_function


def base_function():
    pass
