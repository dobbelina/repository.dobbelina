'''
    Cumination
    Copyright (C) 2022 Team Cumination

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

import json
import re
import xbmc
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse

site = AdultSite('pornkai', "[COLOR hotpink]PornKai[/COLOR]", 'https://pornkai.com/', 'pornkai.png', 'pornkai')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'all-categories', 'Categories', site.img_search)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'api?query={}&sort=best&page=0&method=search', 'Search', site.img_search)
    List(site.url + 'api?query=_best&sort=new&page=0&method=search')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, site.url)

    markup, results_remaining = _extract_markup_and_meta(html)
    if not markup:
        utils.eod()
        return

    soup = utils.parse_html(markup)

    video_items = soup.select('div.thumbnail')

    for item in video_items:
        link = item.select_one('a[href]')
        if not link:
            continue

        videopage = utils.safe_get_attr(link, 'href')
        if not videopage:
            continue
        videopage = utils.fix_url(videopage, site.url)

        title_tag = item.select_one('.trigger_pop, .th_wrap, .title, h2, h3, .name')
        title = utils.safe_get_text(title_tag)
        if not title:
            title = utils.safe_get_attr(link, 'title')
        if not title:
            title = utils.safe_get_text(link)
        title = utils.cleantext(title)
        if not title:
            continue

        img_tag = item.select_one('img')
        img = utils.safe_get_attr(img_tag, 'src', ['data-src', 'data-original', 'data-lazy', 'data-thumbnail'])
        img = utils.fix_url(img, site.url)

        duration = ''
        duration_icon = item.select_one('.fa-clock')
        if duration_icon and duration_icon.parent:
            duration = utils.safe_get_text(duration_icon.parent)
        else:
            duration_tag = item.select_one('.duration, .thumb_time')
            duration = utils.safe_get_text(duration_tag)

        context_url = (utils.addon_sys + "?mode=" + str('pornkai.Related') +
                       "&url=" + urllib_parse.quote_plus(videopage))
        context_menu = [('[COLOR violet]Related videos[/COLOR]', 'RunPlugin(' + context_url + ')')]

        site.add_download_link(title, videopage, 'Playvid', img, title, duration=duration, contextm=context_menu)

    _add_next_page(url, results_remaining)
    utils.eod()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('pornkai.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = url.format(keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    if not cathtml:
        utils.eod()
        return

    soup = utils.parse_html(cathtml)

    category_links = soup.select('a.thumbnail_link, div.thumbnail a[href]')
    for link in category_links:
        caturl = utils.safe_get_attr(link, 'href')
        if not caturl:
            continue

        img_tag = link.select_one('img')
        img = utils.safe_get_attr(img_tag, 'data-src', ['src', 'data-original', 'data-lazy'])
        img = utils.fix_url(img, site.url)

        name_tag = link.select_one('.title, .name, span, strong')
        name = utils.safe_get_text(name_tag) or utils.safe_get_attr(link, 'title') or utils.safe_get_text(link)
        name = utils.cleantext(name)
        if not name:
            continue

        query = ''
        if '?q=' in caturl:
            query = caturl.split('?q=')[-1]
        if query:
            catpage = site.url + 'api?query={}&sort=best&page=0&method=search'.format(query)
        else:
            catpage = utils.fix_url(caturl, site.url)

        site.add_dir(name, catpage, 'List', img)
    utils.eod()


def _extract_markup_and_meta(html):
    if not html:
        return '', None

    results_remaining = None
    markup = html

    try:
        data = json.loads(html)
    except ValueError:
        data = None

    def coerce_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    if isinstance(data, dict):
        candidates = []
        stack = [data]
        seen = set()
        while stack:
            node = stack.pop()
            node_id = id(node)
            if node_id in seen:
                continue
            seen.add(node_id)
            for key, value in node.items():
                if key in ('results_remaining', 'resultsRemaining') and results_remaining is None:
                    results_remaining = coerce_int(value)
                if isinstance(value, str):
                    if '<div' in value or '<a' in value:
                        candidates.append(value)
                elif isinstance(value, dict):
                    stack.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            stack.append(item)
        if candidates:
            markup = candidates[0]

    if isinstance(markup, str):
        markup = (markup
                  .replace('\\n', '\n')
                  .replace('\\t', '\t')
                  .replace('\\"', '"')
                  .replace('\\/', '/'))
    else:
        markup = ''

    return markup, results_remaining


def _add_next_page(url, results_remaining):
    if results_remaining is None or results_remaining <= 0:
        return

    parsed = urllib_parse.urlsplit(url)
    query = urllib_parse.parse_qs(parsed.query)
    try:
        current_page = int(query.get('page', ['0'])[0])
    except (TypeError, ValueError):
        return

    next_page_index = current_page + 1
    display_index = current_page + 2
    last_page = current_page + 2 + (results_remaining // 120)

    query['page'] = [str(next_page_index)]
    encoded_query = urllib_parse.urlencode(query, doseq=True)
    next_url = urllib_parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, encoded_query, parsed.fragment))

    site.add_dir('Next Page ({}/{})'.format(display_index, last_page), next_url, 'List', site.img_next)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex=r'iframe.+?src="([^"]+)"')
    vp.progress.update(25, "[CR]Loading video page[CR]")

    videohtml = utils.getHtml(url, site.url)
    match = re.compile(r'iframe.+?src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        videolink = match[0]
        if 'xh.video' in videolink:
            videolink = utils.getVideoLink(videolink).split('?')[0]
        vp.play_from_link_to_resolve(videolink)
