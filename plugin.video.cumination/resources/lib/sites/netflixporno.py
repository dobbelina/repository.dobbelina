'''
    Cumination
    Copyright (C) 2021 Team Cumination

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
import base64
import requests
import xbmcgui
import xbmcplugin
import json
import sys

from six.moves import urllib_error
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from resources.lib.decrypters.kvsplayer import kvs_decode

progress = utils.progress
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
site = AdultSite('netflixporno', '[COLOR hotpink]NetflixPorno[/COLOR]', 'https://netflixporno.net/', 'netflixporno.png', 'netflixporno')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]XXX Scenes[/COLOR]', site.url + 'scenes/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Parody Movies[/COLOR]', site.url + 'adult/genre/parodies/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Studios[/COLOR]', site.url + 'adult/genre/parodies/', 'Studios', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'adult/genre/parodies/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/', 'Search', site.img_search)
    List(site.url + 'adult')
    utils.eod()


@site.register()
def List(url):
    try:
        listhtml = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    if len(listhtml) == 0:
        listhtml = 'Empty'

    match = re.compile(r'<article class.+?href="([^"]+)".+?(?:data-lazy-src=|\ssrc=)"([^"]+\.jpg[^"]*)".+?title="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for videopage, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, videopage, 'Playvid', img, '')

    nextp = re.compile(r'<a\s*class="next page-numbers"\s*href="([^"]+)', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        nextp = nextp.group(1).replace("&#038;", "&")
        currpg = re.compile(r'class="page-numbers\s*current">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        lastpg = re.compile(r'>([^<]+)</a>\s*<a\s*class="next\s*page', re.DOTALL | re.IGNORECASE).findall(listhtml)[0]
        site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(currpg, lastpg), nextp, 'List', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '+')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    match = re.compile(r'cat-item-\d+"><a href="([^"]+)">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name in match:
        site.add_dir(name, catpage, 'List', site.img_cat)
    utils.eod()


@site.register()
def Studios(url):
    try:
        studhtml = utils.getHtml(url, site.url)
    except urllib_error.URLError as e:
        utils.notify(e)
        return
    match = re.compile(r'director\s*menu-item.+?href="([^"]+)">([^<]+)', re.DOTALL | re.IGNORECASE).findall(studhtml)
    for studpage, name in match:
        site.add_dir(name, studpage, 'List', site.img_cat)
    utils.eod()


def url_decode(str):
    if '/goto/' not in str:
        result = str
    else:
        try:
            result = url_decode(base64.b64decode(re.search('/goto/(.+)', str).group(1)))
        except:
            result = str
    return result


def extract_hlm_root(html):
    m = re.search(r'<div[^>]+class="hlm[^>]*>', html)
    if not m:
        return None
    tag = m.group(0)
    attrs = dict(re.findall(r'(\w[\w-]*)="([^"]*)"', tag))
    return attrs


def extract_servers(html):
    m = re.search(r'data-servers="([^"]+)"', html)
    if not m:
        return []
    raw = m.group(1)
    raw = raw.replace("&quot;", "\"")
    try:
        return json.loads(raw)
    except:
        return []


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    dontask = utils.addon.getSetting("dontask") == "true"

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    r = session.get(url)
    if r.status_code != 200:
        xbmcgui.Dialog().notification("Playvid", "I can't load the page.", xbmcgui.NOTIFICATION_ERROR)
        return

    html = r.text

    root = extract_hlm_root(html)
    if not root:
        xbmcgui.Dialog().notification("Playvid", "Player HLM not found", xbmcgui.NOTIFICATION_ERROR)
        return

    data_rest = root.get("data-rest")
    post_id   = int(root.get("data-post", "0"))
    servers   = extract_servers(html)

    if not servers:
        xbmcgui.Dialog().notification("Playvid", "No servers", xbmcgui.NOTIFICATION_ERROR)
        return

    server_names = [s.get("l", f"Server {i+1}") for i, s in enumerate(servers)]

    if not dontask:
        idx = xbmcgui.Dialog().select("Alege serverul", server_names)
        if idx == -1:
            return
    else:
        idx = 0

    def resolve_server(server):
        if server.get("u"):
            return server["u"]

        api = data_rest + "link"
        payload = {"p": post_id, "h": server["h"]}
        try:
            rr = session.post(api, json=payload)
            j = rr.json()
            return j.get("go", "")
        except:
            return ""

    # Automatic Fallback
    for i in range(idx, len(servers)):
        server = servers[i]
        utils.kodilog(server)
        go = resolve_server(server)
        if go:
            vp.play_from_link_to_resolve(go)
            return

    xbmcgui.Dialog().notification("Playvid", "All servers have failed.", xbmcgui.NOTIFICATION_ERROR)
