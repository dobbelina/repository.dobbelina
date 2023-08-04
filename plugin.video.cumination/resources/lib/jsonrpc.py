"""
    Taken from https://github.com/MikeSiLVO/script.skinshortcuts
    Copyright (C) 2013-2021 Skin Shortcuts (script.skinshortcuts)
    This file is part of script.skinshortcuts
    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from kodi_six import xbmc, xbmcgui
import json

dialog = xbmcgui.Dialog()


def rpc_request(request):
    payload = xbmc.executeJSONRPC(json.dumps(request))
    response = json.loads(payload)
    return response


def validate_rpc_response(response, request=None, required_attrib=None):
    if 'result' in response:
        if not required_attrib:
            return True
        if required_attrib in response['result'] and response['result'][required_attrib]:
            return True

    if 'error' in response:
        message = response['error']['message']
        code = response['error']['code']
        if request:
            error = 'JSONRPC: Requested |%s| received error |%s| and code: |%s|' % \
                    (request, message, code)
        else:
            error = 'JSONRPC: Received error |%s| and code: |%s|' % (message, code)
    else:
        if request:
            error = 'JSONRPC: Requested |%s| received error |%s|' % (request, str(response))
        else:
            error = 'JSONRPC: Received error |%s|' % str(response)

    xbmc.log(error, xbmc.LOGERROR)
    return False


def get_settings():
    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "Settings.getSettings"
    }

    response = rpc_request(payload)
    if not validate_rpc_response(response, payload, 'settings'):
        return None
    return response


def debug_show_log_info(value):
    payload = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "Settings.setSettingValue",
        "params": {
            "setting": "debug.showloginfo",
            "value": value
        }
    }

    response = rpc_request(payload)
    if not validate_rpc_response(response, payload):
        return None
    return response


def toggle_debug():
    settings = get_settings()
    if not settings:
        return False

    result = [x['value'] for x in settings['result']['settings'] if x['id'] == 'debug.showloginfo'][0]
    togglevar = False if result else True
    debug_show_log_info(togglevar)
    return True


def jsonrpc(*args, **kwargs):
    """Perform JSONRPC calls"""

    # We do not accept both args and kwargs
    if args and kwargs:
        return None

    # Process a list of actions
    if args:
        for (idx, cmd) in enumerate(args):
            if cmd.get('id') is None:
                cmd.update(id=idx)
            if cmd.get('jsonrpc') is None:
                cmd.update(jsonrpc='2.0')
        return rpc_request(args)

    # Process a single action
    if kwargs.get('id') is None:
        kwargs.update(id=0)
    if kwargs.get('jsonrpc') is None:
        kwargs.update(jsonrpc='2.0')
    return rpc_request(kwargs)


def has_addon(addonid):
    """Checks if selected add-on is installed."""
    data = jsonrpc(method='Addons.GetAddonDetails', params={'addonid': addonid})
    if 'error' in data:
        # log(3, '{addon} is not installed.', addon=addonid)
        return False

    # log(0, '{addon} is installed.', addon=addonid)
    return True


def addon_enabled(addonid):
    """Returns whether selected add-on is enabled.."""
    data = jsonrpc(method='Addons.GetAddonDetails', params={'addonid': addonid, 'properties': ['enabled']})
    if data.get('result', {}).get('addon', {}).get('enabled'):
        # log(0, '{addon} {version} is enabled.', addon=addonid)
        return True

    # log(3, '{addon} is disabled.', addon=addonid)
    return False


def enable_addon(addonid):
    """Enables selected add-on."""
    data = jsonrpc(method='Addons.SetAddonEnabled', params={'addonid': addonid, 'enabled': True})
    if 'error' in data:
        return False
    return True


def install_addon(addonid):
    """Install addon."""
    from xbmc import executebuiltin
    from xbmcaddon import Addon
    try:
        # See if there's an installed repo that has it
        executebuiltin('InstallAddon({})'.format(addonid), wait=True)
        Addon('{}'.format(addonid))
        return True
    except RuntimeError:
        return False


def check_addon(addonid):
    if not has_addon(addonid):
        ret = dialog.yesno('Kodi Logfile Uploader Missing', 'No Kodi Logfile Uploader found\nDo you want to install it?')  # addon is missing
        if not ret:
            return False
        return install_addon(addonid)
    elif not addon_enabled(addonid):
        ret = dialog.yesno('Kodi Logfile Uploader Disabled', 'Kodi Logfile Uploader is disabled\nDo you want to enable it?')  # addon is disabled
        if not ret:
            return False
        enable_addon(addonid)
    return True
