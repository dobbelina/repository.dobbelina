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
from resources.lib import utils
from resources.lib.adultsite import AdultSite

addon = utils.addon
site = AdultSite("sxyprn", "[COLOR hotpink]Sxy Prn[/COLOR]", "https://sxyprn.com/", "", "sxyprn")


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url, 'Cat', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Networks[/COLOR]', site.url, 'Nets', site.img_cat)
    site.add_dir('[COLOR hotpink]Top Pornstars[/COLOR]', site.url, 'Stars', site.img_cat)
    site.add_dir('[COLOR hotpink]Top rated last week[/COLOR]', site.url + 'popular/top-rated.html', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Top POP last week[/COLOR]', site.url + 'popular/top-pop.html', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Top viewed last week[/COLOR]', site.url + 'popular/top-viewed.html', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Orgasmic[/COLOR]', site.url + 'orgasm/', 'List', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url, 'Search', site.img_search)
    List('https://sxyprn.com/blog/all/0.html?fl=all&sm=latest')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url, site.url)
    if '>Nothing Found. See More...<' in listhtml:
        utils.notify('SEARCH', 'Nothing Found.')
        return

    items = listhtml.split("div class='post_el_small'")
    items.pop(0)
    for item in items:
        iurl, name = re.findall(r"href='([^']+)'\s*title='([^']+)", item)[0]
        if 'http' in name:
            urls = re.findall(r'(http[^\s]+)', name)
            name = re.sub(r'(http[^\s]+)', '', name)
            iurl = '|'.join(urls) + '@'
        else:
            if iurl.startswith('/'):
                iurl = site.url[:-1] + iurl

        info = utils.cleantext(name)
        if name.startswith('#'):
            name = info[1:].split('#')[0]
        else:
            name = info.split('#')[0]
        if 'Cast:' in name:
            name = name.split('Cast:')[0]
        if 'cast:' in name:
            name = name.split('cast:')[0]
        name = name.strip()
        name = name.replace('\n', ' ')
        if name.startswith('{') and name.endswith('}'):
            name = name.strip('{}')

        thumb = quality = duration = ''
        t = re.search(r"data-src='([^']+)", item)
        if t:
            thumb = t.group(1)
            if thumb.startswith('//'):
                thumb = 'http:' + thumb
        else:
            t = re.search(r"src='([^']+)", item)
            if t:
                thumb = t.group(1)
                if thumb.startswith('//'):
                    thumb = 'http:' + thumb

        t = re.search(r"duration_small.+?';?>([\d:]+)", item)
        if t:
            duration = t.group(1) if ':' in t.group(1) else ''

        t = re.search(r"bitrate.+?';?>([^<]+)", item)
        if t:
            quality = t.group(1)

        site.add_download_link(name, iurl, 'Playvid', thumb, info, duration=duration, quality=quality)

    if "class='ctrl_el'" in listhtml:
        if '/popular/' in url or '/orgasm/' in url:
            currpage = re.findall(r"class='ctrl_el\s*ctrl_sel'>([^<]+)", listhtml)[0]
            lastpage = re.findall(r"class='ctrl_el'>([^<]+)", listhtml)[-1]
            if int(currpage) < int(lastpage):
                npage = re.findall(r"class='ctrl_el\s*ctrl_sel'>.+?href='([^']+)", listhtml)[0]
                if npage.startswith('/'):
                    npage = site.url[:-1] + npage
                site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(currpage, lastpage), npage, 'List', site.img_next)
        else:
            npage = re.search(r"href='([^']+)'\s*class='tdn'><div\s*class='next_page", listhtml)
            if npage:
                npage = npage.group(1)
                if npage.startswith('/'):
                    npage = site.url[:-1] + npage
                currpage = re.findall(r"class='ctrl_el\s*ctrl_sel'>([^<]+)", listhtml)[0]
                lastpage = re.findall(r"class='ctrl_el'>([^<]+)", listhtml)[-1]
                site.add_dir('Next Page... (Currently in Page {0} of {1})'.format(currpage, lastpage), npage, 'List', site.img_next)

    utils.eod()


def ssut51(j):
    j = re.sub(r'\D', '', j)
    sut = 0
    for i in range(len(j)):
        sut += int(j[i])
    return sut


@site.register()
def Cat(url):
    cathtml = utils.getHtml(url, site.url)
    cats = re.compile(r"href='([^']+)'><div\s*class='htag_el'.+?data-src='([^']+).+?#([^<]+).+?count'>([^<]+)").findall(cathtml)
    for caturl, img, name, count in cats:
        name += ' [COLOR deeppink]({0})[/COLOR]'.format(count)
        caturl = site.url[:-1] + caturl
        img = 'http:' + img
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Nets(url):
    cathtml = utils.getHtml(url, site.url)
    cats = re.compile(r"href='([^']+)'\s*target='_blank'><div\s*class='top_sub_el\s*top_sub_el_sc'><span\s*class='top_sub_el_key_sc'>([^<]+)").findall(cathtml)
    for caturl, name in cats:
        caturl = site.url[:-1] + caturl
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Stars(url):
    cathtml = utils.getHtml(url, site.url)
    cats = re.compile(r"href='([^']+)'\s*target='_blank'><div\s*class='top_sub_el\s*top_sub_el_ps'><span\s*class='top_sub_el_key_ps'>([^<]+)").findall(cathtml)
    for caturl, name in cats:
        caturl = site.url[:-1] + caturl
        site.add_dir(name, caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '_')
        searchUrl = searchUrl + title + '.html'
        List(searchUrl)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videourl = ''

    if url.endswith('@'):
        links = url[:-1].split('|')
        links = {utils.get_vidhost(link): link for link in links if vp.resolveurl.HostedMediaFile(link)}
        videourl = utils.selector('Select link', links)
    else:
        videopage = utils.getHtml(url, site.url)
        videourl = re.compile('''data-vnfo='{".+?":"(.+?)"''', re.DOTALL | re.IGNORECASE).findall(videopage)[0].replace(r'\/', '/')
        tmpfile = videourl.split('/')
        tmpfile[5] = str(int(tmpfile[5]) - ssut51(tmpfile[6]) - ssut51(tmpfile[7]))
        videourl = '/'.join(tmpfile)
        videourl = site.url[:-1] + videourl.replace('/cdn/', '/cdn8/')

    if not videourl:
        utils.notify('Oh Oh', 'No Videos found')
        vp.progress.close()
        return

    if '/cdn8/' in videourl:
        videourl = utils.getVideoLink(videourl)
        if videourl.startswith('//'):
            videourl = 'https:' + videourl
        vp.play_from_direct_link(videourl)
    else:
        vp.play_from_link_to_resolve(videourl)
