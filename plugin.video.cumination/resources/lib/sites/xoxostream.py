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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('xoxo', '[COLOR hotpink]XOXOstream[/COLOR]', 'https://xoxostream.com/', 'xoxostream.png', 'xoxo')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/', 'Models', site.img_models)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_tags)

    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/{}/1/', 'Search', site.img_search)    
    List(site.url + '1/')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'<li id=.+?href="([^"]+)" title="([^"]+)".+?src="([^"]+)".+?duration.+?;([^;]+)</span', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if not match:
        utils.notify("XOXOstream", "No video found!")
        return
    for videopage, name, img, duration  in match:
        name = utils.cleantext(name)
        videopage = "https:" + videopage if videopage.startswith("/") else videopage
        site.add_download_link(name, videopage, 'Playvid', img, name, duration=duration)

    np = re.search(
        r'<a[^>]*class="next page-numbers"[^>]*href="\.\./(\d+)/"',
        listhtml
    )

    if np:
        np = np.group(1)
        parts = url.rstrip("/").split("/")
        base = "/".join(parts[:-1]) + "/" + np + '/'
        site.add_dir('Next Page... ({0})'.format(np), base, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url.format(keyword.replace(' ', '_'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")    
    html = utils.getHtml(url)

    m = re.search(r'<p id="description" class="([^"]+)"', html)
    if not m:
        raise ValueError("No videolink found!")

    class_data = m.group(1).split()

    m_val        = class_data[0]
    d_val        = class_data[1]
    q_val        = class_data[2]
    tid          = class_data[3]
    quality      = class_data[4]
    secure_token = class_data[5]
    timestamp    = class_data[6]

    video_url = (
        f"https://vdownload-{m_val}.sb-cd.com/"
        f"{d_val}/{q_val}/{tid}-{quality}.mp4"
        f"?secure={secure_token},{timestamp}"
        f"&m={m_val}&d={d_val}&_tid={tid}"
    )

    vp.play_from_direct_link(video_url)


@site.register()
def Tags(url):
    html = utils.getHtml(url)
    container = re.compile(r'<ul class="tags_list">(.*?)</ul>', re.DOTALL | re.IGNORECASE).search(html)

    m = re.compile(r'<li>.+?href="([^"]+)".+?>([^>]+)<', re.DOTALL | re.IGNORECASE).findall(container.group(1))
    if not m:
        raise ValueError("No Tags found!")
    for tag_url, tag in m:
        site.add_dir('[COLOR hotpink]{}[/COLOR]'.format(tag), site.url + 'tags/' + tag_url, 'List', site.img_search)
    utils.eod()

@site.register()
def Models(url):
    html = utils.getHtml(url)
    m = re.compile(r'<li>.+?href="([^"]+)".+?src="([^"]+)".+?>([^>]+)<', re.DOTALL | re.IGNORECASE).findall(html)
    if not m:
        raise ValueError("No Tags found!")
    for tag_url, img, tag in m:
        if '/models/'  not in img:
            continue
        img = site.url + img.strip('../')
        site.add_dir('[COLOR hotpink]{}[/COLOR]'.format(tag), site.url + 'tags/' + tag_url, 'List', img)
    utils.eod()
