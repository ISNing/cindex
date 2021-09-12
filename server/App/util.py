import json
import logging
import os
import traceback
from json.decoder import JSONDecodeError
from typing import IO

import rsa
from flask import request

default_global_conf = {
    'configuration': {
        'blu_imports': [],
        'database_uri': 'sqlite:///../{work_dir}/db.sqlite',
        'url_host': 'http://please_edit_url_host_in_config/',
        'flask_config': {},
        'server_name': None,
        'secret_key': str(os.urandom(24)),
        'work_dir': 'data/'
    }
}
temp_state = {}

conf = {}
conf_folder_path = os.getcwd()
conf_file_path = os.path.join(conf_folder_path, 'conf.json')

logger = logging.getLogger(__name__)


def __get_conf():
    """
    Get conf
    :return: conf <dict>
    """
    f_fok = os.access(conf_file_path, os.F_OK)
    f_rok = os.access(conf_file_path, os.R_OK)
    f_wok = os.access(conf_file_path, os.W_OK)
    flag = False
    flag_c = False
    while True:
        if f_fok and f_rok and f_wok:
            with open(conf_file_path, 'r') as f:
                global conf
                conf = json.load(f)
                break
        else:
            if not f_fok:
                if flag:
                    logger.critical('\'{}\' create failed'.format(conf_file_path))
                    flag_c = True
                elif os.access(conf_folder_path, os.W_OK):
                    with open(conf_file_path, 'w') as f:
                        json.dump({}, f)
                else:
                    logger.critical('\'{}\' is not writeable'.format(conf_folder_path))
                    flag_c = True
            elif not f_rok:
                logger.critical('\'{}\' is not readable'.format(conf_file_path))
                flag_c = True
            elif not f_wok:
                logger.critical('\'{}\' is not writeable'.format(conf_file_path))
                flag_c = True
        if flag_c:
            exit(1)
        flag = True
        f_fok = os.access(conf_file_path, os.F_OK)
        f_rok = os.access(conf_file_path, os.R_OK)
        f_wok = os.access(conf_file_path, os.W_OK)
    return conf


def __set_conf(obj: dict):
    """
    Write conf into file

    :param obj: conf will be write in to file <dict>
    """
    __get_conf()  # Check permissions of conf file
    with open(conf_file_path, 'w') as f:
        json.dump(obj, f, sort_keys=True, indent=4, separators=(',', ': '))


def dict_get(dic: dict, locators: list, default=None, err_msg=None):
    """
    Get value of the dict by a list locators

    If you don't want to get the error log, please make err_msf False.

    :param dic: The dict which you want to get value <dict>
    :param locators: Locators, like:['result', 'msg', '-1', 'status'] <list>
    :param default: Value will return when error happened.(default: None) <any>
    :param err_msg: Message will be logged when error happened. <str>
    :return: The value we've got <any>
    """

    flag_e = err_msg

    if not isinstance(dic, dict) or not isinstance(locators, list):
        return default

    value = None

    for locator in locators:
        if not type(value) in [dict, list] and isinstance(locator, str):
            try:
                value = (dic.copy()[locator])
                continue
            except KeyError as e:
                if flag_e:
                    logger.warning(e if err_msg is None else err_msg)
                return default
        elif isinstance(value, dict):
            try:
                value = dict_get(value, [locator])
            except KeyError:
                return default
            continue
        elif isinstance(value, list) and isinstance(locator, int):
            try:
                value = value[locator]
            except IndexError as e:
                if flag_e:
                    logger.warning((repr(e) + '\n' + str(traceback.format_exc())) if err_msg is None else err_msg)
                return default
            continue
        elif isinstance(value, dict):
            try:
                value = dict_get(value, [locator])
            except KeyError:
                return default

    return value


def dict_set(dic: dict, locators: list, target):
    """
    Set value of the dict by a list locators

    :param dic: The dict which you want to set value <dict>
    :param locators: Locators,like:['result', 'msg', '-1', 'status'] <list>
    :param target: Target value <any>
    :return: Dict which the target value have changed <dict>
    """

    if not isinstance(dic, dict) or not isinstance(locators, list):
        raise ValueError

    for i in range(len(locators) - 1, -1, -1):
        if isinstance(locators[i], str) and locators[i].startswith('arr:'):
            try:
                locators[i] = int(locators[i].lstrip('arr:'))
            except ValueError:
                pass

    cur_val = target
    for i in range(len(locators) - 1, -1, -1):
        if isinstance(locators[i], str) or isinstance(locators[i], int):
            if i == 0:
                new_val = dic.copy()
            else:
                new_val = dict_get(dic.copy(), locators[:i])
            if new_val is None:
                new_val = {locators[i]: cur_val}
            else:
                new_val[locators[i]] = cur_val
            cur_val = new_val
            continue
    return cur_val


def check_val_list(locators: list, default):
    """
    Check whether a value is available or not in conf(Locate with a list locater)
    If not, insert it with the value of default.
    :param locators: 
    :param default: default value will be inserted if val not found
    :return: True if found conf ready
    """
    dic = __get_conf()
    pkg = ''
    for locator in locators:
        if pkg == '':
            pkg += locator
        else:
            pkg += '.{}'.format(locator)
    if dict_get(dic, locators, err_msg='There\'s no "{}" key in config file,inserting...'.format(pkg)) is None:
        __set_conf(dict_set(dic, locators, default))
        return False
    else:
        return True


def check_val_str(locators: str, default):
    check_val_list(list(locators.split('.')), default)


def get_conf_checked(locators: str, default, cb=None):
    locators = list(locators.split('.'))
    found_conf = check_val_list(locators, default)
    if cb is not None:
        cb(found_conf)
    return dict_get(__get_conf(), locators)


def gen_get_conf_checked(locators: str, default):
    l = locators

    def wrapper(locators: str, default_val=None, cb=None):
        if default_val is None:
            default_val = dict_get(default, list(locators.split(".")))
        locators = l + "." + locators
        locators_list = list(locators.split('.'))
        found_conf = check_val_list(locators_list, default_val)
        if cb is not None:
            cb(found_conf)
        return dict_get(__get_conf(), locators_list)

    return wrapper


def get_conf(locators: str):
    locators = list(locators.split('.'))
    return dict_get(__get_conf(), locators)


def set_part_conf_list(locators: list, target: any):
    __set_conf(dict_set(__get_conf(), locators, target))


def set_part_conf_str(locators: str, target: any):
    set_part_conf_list(list(locators.split('.')), target)


def get_global_conf():
    global_conf = get_conf_checked('global', default_global_conf)
    return global_conf


def get_list_changed(oldList: iter, newList: iter):
    """
    Get changed items between oldList and newList

    :param oldList: Old list
    :param newList: New list
    :return: result[0]: items in oldList which not found in newList
     result[1]: items in newList which not found in oldList
    """
    result = ([], [])
    for oldDict in oldList:
        flag = False
        if flag:
            break
        for newDict in newList:
            if flag:
                break
            if oldDict == newDict:
                flag = True
        result[0].append(oldDict)
    for newDict in newList:
        flag = False
        if flag:
            break
        for oldDict in oldList:
            if flag:
                break
            if newDict == oldDict:
                flag = True
        result[1].append(newDict)
    return result


def get_post_data():
    """
    Get data from post request
    :return:
    """
    data = {}
    if request.content_type.startswith('application/json') if request.content_type else False:
        data = request.data
        try:
            data = json.loads(data)
        except JSONDecodeError:
            from App.errors import InvalidJSONSyntaxException
            raise InvalidJSONSyntaxException()
    else:
        for key, value in request.form.items():
            if key.endswith('[]'):
                data[key[:-2]] = request.form.getlist(key)
            else:
                data[key] = value

    return data


def read_file_content(f_path: str, cb: callable):
    """
    Get file's content with permission checked
    :param f_path: The path of file <str>
    :param cb: Callback when file not readable <function>
    :return: The content of the file<str>
    """
    f_path = get_path_relate_from_work_dir(f_path)
    f_folder_path = os.path.dirname(f_path)
    f_fok = os.access(f_path, os.F_OK)
    f_rok = os.access(f_path, os.R_OK)
    f_wok = os.access(f_path, os.W_OK)
    flag = False
    flag_c = False
    global temp_state
    temp_state['cb_called'] = False
    while True:
        if f_fok and f_rok and f_wok:
            if cb and not temp_state['cb_called']:
                f = open(f_path, 'a')
                cb(True, f)
                temp_state['cb_called'] = True
            with open(f_path, 'r') as f:
                global conf
                return f.read()
        else:
            if not f_fok:
                if not os.path.exists(f_folder_path):
                    logger.warning('Folder \'{}\' does not exists, creating...'.format(f_folder_path))
                    os.makedirs(f_folder_path, 0o755, True)
                if flag:
                    logger.critical('\'{}\' create failed'.format(f_path))
                    flag_c = True
                elif os.access(f_folder_path, os.W_OK):
                    if cb and not temp_state['cb_called']:
                        f = open(f_path, 'x')
                        cb(False, f)
                        temp_state['cb_called'] = True
                else:
                    logger.critical('\'{}\' is not writeable'.format(f_folder_path))
                    flag_c = True
            elif not f_rok:
                logger.critical('\'{}\' is not readable'.format(f_path))
                flag_c = True
            elif not f_wok:
                logger.critical('\'{}\' is not writeable'.format(f_path))
                flag_c = True
        if flag_c:
            exit(1)
        flag = True
        f_fok = os.access(f_path, os.F_OK)
        f_rok = os.access(f_path, os.R_OK)
        f_wok = os.access(f_path, os.W_OK)


def new_keys(nbits: int):
    """
    Generates public and private keys, and returns them as (pub, priv)

    :param nbits: the number of bits required to store ``n = p*q``.
    :return: a tuple (PublicKey, PrivateKey)
    """
    (pubkey, privkey) = rsa.newkeys(nbits)
    pub = pubkey.save_pkcs1()
    priv = privkey.save_pkcs1()
    return pub, priv


def get_keys(pub_key_path, priv_key_path):
    global temp_state

    def pub_cb(result, f):
        global temp_state
        temp_state['readable'] = result
        temp_state['pub_f'] = f

    def priv_cb(result, f):
        global temp_state
        temp_state['readable'] = result
        temp_state['priv_f'] = f

    pub_str = read_file_content(pub_key_path, pub_cb)
    priv_str = read_file_content(priv_key_path, priv_cb)
    while not temp_state['readable']:
        (pub_bytes, priv_bytes) = new_keys(2048)
        temp_state['pub_f'].write(str(pub_bytes))
        temp_state['pub_f'].close()
        temp_state['priv_f'].write(str(priv_bytes))
        temp_state['priv_f'].close()
        pub_str = read_file_content(pub_key_path, pub_cb)
        priv_str = read_file_content(priv_key_path, priv_cb)
    if not temp_state['readable']:
        raise PermissionError('Found key files but cannot read it')
    return pub_str, priv_str


def get_work_dir():
    return get_global_conf()["configuration"]['work_dir'].rstrip("/") + '/'


def get_database_uri():
    return get_global_conf()['configuration'].get('database_uri').format(
        work_dir=get_work_dir().lstrip('/').rstrip("/"))


def composed(decs: list, is_reversed=False):
    """
    Combine multiple decorators into one decorators
    In default, the decorators will be applied as the order in the list "decs"

    :param decs: Multiple decorators which is expected to be combined
    :param is_reversed: Will the apply order of the decorators be reversed.
    :return: The decorator combined
    """

    def deco(f):
        if is_reversed:
            for dec in reversed(decs):
                f = dec(f)
        else:
            for dec in decs:
                f = dec(f)
        return f

    return deco


def get_path_relate_from_work_dir(p):
    return p if os.path.isabs(p) else os.path.join(get_work_dir() + p)
