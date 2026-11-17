'''
    Cumination
    Copyright (C) 2026 Team Cumination

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
import html as html_module
import urllib.parse as urllib_parse
import xbmc
import xbmcgui

from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('3movs', '[COLOR hotpink]3Movs[/COLOR]', 'https://www.3movs.com/', '3movs.png', '3movs')

movs_headers = utils.base_hdrs.copy()
movs_headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.3movs.com/',
})


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search_videos/?q=', 'Search', site.img_search)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Most Viewed[/COLOR]', site.url + 'most-viewed/all-time/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Rated[/COLOR]', site.url + 'top-rated/all-time/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Longest[/COLOR]', site.url + 'longest/', 'List', site.img_cat)
    List(site.url + 'latest-updates/1/')
    utils.eod()


@site.register()
def List(url, page=1):
    xbmcgui.Dialog().textviewer(url, url)
    if page is None:
        page = 1
    else:
        try:
            page = int(page)
        except:
            page = 1

    current_url = url
    if page > 1:
        if '/search_videos/' in url and '?' in url:
            base, query_str = url.split('?', 1)
            current_url = f"{base.rstrip('/')}/{page}/?{query_str}"
        else:
            current_url = f"{url.rstrip('/')}/{page}/"

    try:
        html = utils.getHtml(current_url, site.url, headers=movs_headers)
    except:
        utils.notify('Error', 'Failed to load page')
        utils.eod()
        return

    if not html:
        utils.notify('Error', 'No content found')
        utils.eod()
        return

    blocks = re.split(r'<div[^>]+class=["\'][^"\']*item thumb', html)[1:]

    for block in blocks:
        v_url_match = re.search(r'href=["\'](https?://www\.3movs\.com/videos/[^"\']+)["\']', block)
        v_title_match = re.search(r'title=["\']([^"\']+)["\']', block)
        v_thumb_match = re.search(r'data-src=["\']([^"\']+)["\']', block)
        v_duration_match = re.search(r'<div[^>]+time[^>]*>([^<]+)</div>', block)

        if v_url_match and v_title_match:
            v_url = v_url_match.group(1)
            v_title = html_module.unescape(v_title_match.group(1))
            v_thumb = v_thumb_match.group(1) if v_thumb_match else site.img_cat
            v_duration = v_duration_match.group(1).strip() if v_duration_match else ""

            # # Ajouter la durée au titre
            # name = v_title
            # if v_duration:
            #     name += ' [COLOR hotpink][' + v_duration + '][/COLOR]'

            site.add_download_link(v_title, v_url, 'Playvid', v_thumb, v_title, duration=v_duration)

    if 'data-parameters="' in html:
        match = re.findall('class="item active".+?class="item.+?(?:href="#search".+?data-parameters="|href=")([^"]+(\d+))"', html, re.DOTALL)
        q = match[0][0].split(';')[0].replace(':', '=')
        f = match[0][0].split(';')[3].split('+')[0] + '=' + match[0][1]
        npurl = site.url + 'search_videos/?' + q + '&' + f
        npnr = match[0][1]
        pages = [int(x) for x in re.findall(r'title="Page\s+(\d+)"', html)]
        lpnr = max(pages)
        # cm_page = (utils.addon_sys + "?mode={}.GotoPage".format(site.name) + "&url=" + urllib_parse.quote_plus(npurl) + "&np=" + str(npnr) + "&lp=" + str(lpnr))
        # cm = [('[COLOR violet]Goto Page #[/COLOR]', 'RunPlugin(' + cm_page + ')')]

        site.add_dir('[COLOR hotpink]Next Page ({0}/{1})[/COLOR]'.format(npnr, lpnr), npurl, 'List', site.img_next) #, contextm=cm)
    else:
        re_npurl = r'class="item active".+?class="item.+?href="([^"]+)"'
        re_npnr = r'class="item active".+?class="item.+?href="[^"]*.?(\d+)/"'
        re_lpnr = r'class="item"><a\shref=".+?><a\shref="[^"]*.?/(\d+)/"'
        utils.next_page(site, '{}.List'.format(site.name), html, re_npurl, re_npnr, re_lpnr=re_lpnr)    #, contextm='{}.GotoPage'.format(site.name))

    utils.eod()


@site.register()
def Categories(url):
    try:
        cathtml = utils.getHtml(url, site.url, headers=movs_headers)
    except:
        utils.notify('Error', 'Failed to load categories')
        utils.eod()
        return

    cat_pattern = r'<div[^>]+thumb_cat item[^>]*>.*?<a[^>]+href=["\'](https?://www\.3movs\.com/categories/[^"\']+)["\'][^>]+title=["\']([^"\']+)["\'].*?data-src=["\']([^"\']+)["\'].*?<div[^>]+title[^>]*>(.*?)</div>'
    cats = re.findall(cat_pattern, cathtml, re.DOTALL)

    cat = []
    for c_url, c_title, c_thumb, c_inner_html in cats:
        count_match = re.search(r'<span>([^<]+)</span>', c_inner_html)
        count = count_match.group(1) if count_match else ""
        c_url = site.url + 'search_videos/?q=' + c_title
        display_title = f"{html_module.unescape(c_title)} [COLOR hotpink]({count})[/COLOR]"
        cat.append((display_title, c_url, c_thumb))
    for item in sorted(cat, key=lambda x: x[0]):
        site.add_dir(item[0], item[1], 'List', item[2])
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        search_url = site.url + 'search_videos/?q=' + keyword.replace(' ', '-')
        List(search_url, 1)  # Ajoute juste le paramètre page ici


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")

    try:
        page_html = utils.getHtml(url, site.url, headers=movs_headers)
    except:
        vp.progress.close()
        utils.notify('Error', 'Failed to load video page')
        return

    player_config = re.search(r'var\s+flashvars\s*=\s*({.*?});', page_html, re.DOTALL)
    stream_url = None

    if player_config:
        config_json = player_config.group(1)
        hq_match = re.search(r'video_url:\s*[\'"](.*?)[\'"]', config_json)
        lq_match = re.search(r'video_alt_url:\s*[\'"](.*?)[\'"]', config_json)

        hq_url = hq_match.group(1) if hq_match else None
        lq_url = lq_match.group(1) if lq_match else None

        stream_url = hq_url or lq_url

    if stream_url:
        stream_url += '|User-Agent={0}&Referer={1}'.format(
            utils.USER_AGENT,
            site.url
        )
        vp.play_from_direct_link(stream_url)
        vp.progress.close()
    else:
        vp.progress.close()
        utils.notify(name, utils.i18n('not_found'))

@site.register()
def GotoPage(url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        if '=' in url:
            url = re.sub(r'=\d+?$', f'={pg}', url)
        else:
            url = re.sub(r'/\d+/?$', f'/{pg}/', url)
        xbmcgui.Dialog().textviewer('GoToPage', url)
        # url = url.replace('/{}/?'.format(np), '/{}/?'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode={}.List".format(site.name) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')
