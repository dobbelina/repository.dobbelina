'''
    Cumination
    Copyright (C) 2015 Whitecream

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import hashlib
import time
from resources.lib.basics import addon
from resources.lib.utils import dialog, i18n
from resources.lib.url_dispatcher import URL_Dispatcher
from kodi_six import xbmcgui

url_dispatcher = URL_Dispatcher('pin')


@url_dispatcher.register()
def SetPin():
    selected = dialog.select(i18n('choose_option'), [i18n('set_pin'), i18n('remove_pin')])
    if selected == -1:
        return
    elif selected == 0:
        pincode = AskPin()
        if pincode:
            addon.setSetting('pincode', pincode)
            addon.setSetting('logintime', '')
    elif selected == 1:
        addon.setSetting('pincode', '')
        addon.setSetting('logintime', '')
    return


def AskPin():
    pincode = dialog.input(i18n('enter_pin'), option=xbmcgui.ALPHANUM_HIDE_INPUT)
    if pincode:
        return HashPin(pincode)
    return False


def HashPin(pin):
    pinhash = hashlib.sha256(pin.encode('ascii'))
    return pinhash.hexdigest()


def CheckPin():
    now = time.time()
    hashedpin = addon.getSetting('pincode')
    logintime = addon.getSetting('logintime')
    if not logintime:
        logintime = 0
    timecheck = now - (60 * 60)
    if not float(logintime) < timecheck:
        return True
    if hashedpin:
        pinhash = AskPin()
        if pinhash == hashedpin:
            addon.setSetting('logintime', str(now))
            return True
        else:
            retry = dialog.yesno(i18n('pin_incorrect'), '{0}[CR]{1}?'.format(i18n('incorrect_msg'), i18n('retry')), yeslabel=i18n('retry'))
            if retry:
                return CheckPin()
            else:
                return False
    return True
