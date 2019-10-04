'''
    Ultimate Whitecream
    Copyright (C) 2018 holisticdioxide

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

import xbmcplugin
from resources.lib import utils
from elreyx import EXList

@utils.url_dispatcher.register('160')
def Main():
    '''
    Content is the same as Elreyx, with almost the same layout and English descriptions.
    Used functions are defined in elreyx.py
    '''
    utils.addDir('[COLOR hotpink]Categories[/COLOR]', 'http://www.videomegaporn.com/index.html', 113, '', '')
    utils.addDir('[COLOR hotpink]Search[/COLOR]', 'http://www.videomegaporn.com/search-', 114, '', '')
    EXList('http://www.videomegaporn.com/index.html')
    xbmcplugin.endOfDirectory(utils.addon_handle)
