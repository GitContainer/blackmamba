#!python3

from objc_util import ObjCClass, on_main_thread
import time
import os
import json
import requests
from blackmamba.log import info, error
from blackmamba.config import get_config_value
import blackmamba.system as system


_DEFAULTS_LAST_UPDATE_CHECK_KEY = 'BlackMambaLastUpdateCheck'
_ROOT_DIR = os.path.expanduser('~/Documents/site-packages-3/blackmamba')
_RELEASE_PATH = os.path.join(_ROOT_DIR, '.release.json')
_OWNER = 'zrzka'
_REPOSITORY = 'blackmamba'
_INSTALL_COMMAND = 'import requests as r; exec(r.get(\'http://bit.ly/get-blackmamba\').text)'


def _user_defaults():
    NSUserDefaults = ObjCClass('NSUserDefaults')
    return NSUserDefaults.standardUserDefaults()


@on_main_thread
def _get_last_update_check():
    return _user_defaults().integerForKey_(_DEFAULTS_LAST_UPDATE_CHECK_KEY)


@on_main_thread
def _set_last_update_check(timestamp):
    _user_defaults().setInteger_forKey_(timestamp, _DEFAULTS_LAST_UPDATE_CHECK_KEY)


def _timestamp():
    return int(time.time())


def get_local_release():
    try:
        with open(_RELEASE_PATH, 'rt') as input:
            return json.load(input)
    except Exception:
        pass


def _url(command):
    return 'https://api.github.com/repos/{}/{}/{}'.format(_OWNER, _REPOSITORY, command)


def _request(method, command):
    url = _url(command)
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }

    return requests.request(method, url, headers=headers)


def _get(command):
    return _request('GET', command)


def _get_json(command):
    return _get(command).json()


def _get_latest_release():
    try:
        return _get_json('releases/latest')
    except Exception:
        pass


def check():
    if not get_config_value('update.enabled', True):
        return

    timestamp = _timestamp()
    last_check = _get_last_update_check() or timestamp
    if last_check + get_config_value('update.interval', 86400) > timestamp:
        return
    _set_last_update_check(timestamp)

    info('Checking for Black Mamba updates...')

    local_release = get_local_release()
    latest_release = _get_latest_release()

    if not latest_release:
        error('Failed to fetch latest release version info')
        return

    if local_release:
        if local_release['tag_name'] == latest_release['tag_name']:
            info('No updates available, you are up to date')
            return

        info('New version available, selfupdate.py will be executed')
        import blackmamba.ide.script as script
        if system.PYTHONISTA_BUNDLE_VERSION >= 311015:
            # 311015 introduced script queues, no need for delay
            delay = None
        else:
            delay = 0.5
        script.run_script('site-packages-3/blackmamba/script/selfupdate.py', delay=delay)

    else:
        info('Missing installed version info, you should use the installer')
