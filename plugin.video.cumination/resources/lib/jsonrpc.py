"""
    Taken from https://github.com/MikeSiLVO/script.skinshortcuts
    Copyright (C) 2013-2021 Skin Shortcuts (script.skinshortcuts)
    This file is part of script.skinshortcuts
    SPDX-License-Identifier: GPL-2.0-only
    See LICENSES/GPL-2.0-only.txt for more information.
"""

from kodi_six import xbmc
import json


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
