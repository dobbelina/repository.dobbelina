'''
    Cumination
    Copyright (C) 2023 Team Cumination

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

import re
import xbmc
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('iflix', '[COLOR hotpink]Iflix[/COLOR]', 'http://www.incestflix.com/', 'http://sist3r.incestflix.com/img/wwwincestflixcom.png', 'iflix')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Sub-genres, Sub-fetishes, Themes[/COLOR]', site.url + 'alltags/sub', 'tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Relations[/COLOR]', site.url + 'alltags/relations', 'tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Ethnicities, Nationalities, Sects & Religious Groups[/COLOR]', site.url + 'alltags/ethn', 'tags', site.img_cat)
    site.add_dir('[COLOR hotpink]General, Other, Not Categorized[/COLOR]', site.url + 'alltags/general', 'tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Actresses, Performers[/COLOR]', site.url + 'alltags/actresses', 'tags', site.img_cat)
    List(site.url + 'page/1')
    utils.eod()


@site.register()
def List(url):
    utils.kodilog(url)
    listhtml = utils.getHtml(url, '')
    match = re.compile(r"<a id='videolink' href='([^']+)'><[^>]+>([^<]+)<.*?url\(([^\)]+)\);", re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        return
    for videopage, name, img in match:
        name = utils.cleantext(name)
        videopage = 'http:' + videopage if videopage.startswith('//') else videopage
        img = 'http:' + img if img.startswith('//') else img
        contextmenu = []
        contexturl = (utils.addon_sys
                          + "?mode=" + str('iflix.Lookupinfo')
                          + "&url=" + urllib_parse.quote_plus(videopage))
        contextmenu.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + contexturl + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=contextmenu)

    page = int(url.split('/')[-1])
    npage = page + 1
    if 'page/{0}'.format(npage) in listhtml:
        npage_url = url.replace('page/{0}'.format(page), 'page/{0}'.format(npage))
        site.add_dir('Next Page ({0})'.format(npage), npage_url, 'List', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    video_page = utils.getHtml(url, site.url)

    source = re.compile("""<source.*?src=(?:"|')([^"']+)[^>]+>""", re.DOTALL | re.IGNORECASE).search(video_page)
    if source:
        videourl = source.group(1)
        videourl = 'http:' + videourl if videourl.startswith('//') else videourl
        vp.play_from_direct_link(videourl)
    else:
        vp.progress.close()
        utils.notify('Oh Oh', 'No Videos found')
        return


@site.register()
def tags(url):
    what = url.split('/')[-1]
    url = '/'.join(url.split('/')[:-1])
    listhtml = utils.getHtml(url)
    
    if what == 'sub':
        listhtml = re.compile("Themes</h1>(.*?)<h1>", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    elif what == 'relations':
        listhtml = re.compile("<h1>Relations</h1>(.*?)<h1>", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    elif what == 'ethn':
        listhtml = re.compile("Religious Groups</h1>(.*?)<h1>", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    elif what == 'general':
        listhtml = re.compile("Not Categorized</h1>(.*?)<h1>", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    elif what == 'actresses':
        listhtml = re.compile("Performers</h1>(.*?)</div>", re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
    
    
    match = re.compile("href='([^']+)'><span id='studiolink[^>]+>(.*?)</span", re.DOTALL | re.IGNORECASE).findall(listhtml)
    for tagpage, name in match:
        name = utils.cleantext(name.strip()).replace('<b>', '[COLOR red][B]').replace('</b>', '[/B][/COLOR]')
        tagpage = 'http:' + tagpage if tagpage.startswith('//') else tagpage
        site.add_dir(name, tagpage + '/page/1', 'List', '')

    utils.eod()


@site.register()
def Lookupinfo(url):
    class SiteLookup(utils.LookupInfo):
        def url_constructor(self, url):
            url = 'http:' + url if url.startswith('//') else url
            return url + '/page/1'

    lookup_list = [
        ("Tag", r"<a class='studiolink\d+' href='([^']+)'>([^<]+)</a>", '')
    ]

    lookupinfo = SiteLookup(site.url, url, 'iflix.List', lookup_list)
    lookupinfo.getinfo()