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

site = AdultSite('superporn', '[COLOR hotpink]SuperPorn[/COLOR]', 'https://www.superporn.com/', 'superporn.png', 'superporn')

addon = utils.addon


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url +'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url +'pornstars/', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Porn series[/COLOR]', site.url +'series/', 'PornSeries', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search?q=', 'Search', site.img_search)
    List(site.url + '?page=1')


@site.register()
def List(url):
    listhtml = utils.getHtml(url)    
    pattern = re.compile(
        r'class="thumb-video .+?\s* href="([^"]+)".*?'                           
        r'data-src="([^"]+)".*?'                                                      
        r'class="duracion">\s*([^<\n][^<]*?)\s*</span>\s.*?'                          
        r'<a[^>]*class="thumb-video__description"[^>]*>(.*?)</a>'                     
        , re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    matches = pattern.findall(listhtml)
    for videopage, img, duration, name in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + duration.strip() + '][/COLOR]'

        site.add_download_link(name, videopage, 'Playvid', img, name)

    np = re.compile(r'pagination_item--next.*?href="([^"]*?(\d+)[^"]*)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        site.add_dir('Next Page... ({0})'.format(nextpage), nplink, 'List', site.img_next)
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url += keyword.replace(' ', '+')
        List(url)

@site.register()
def Categories(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'<div class="thumb-video[^"]*"[^>]*>'
        r'.*?href="([^"]+)"'                
        r'.*?data-src="([^"]+)"'           
        r'.*?<h3[^>]*>([^<]+)</h3>'       
        r'.*?>([\d,]+)\s*videos'         
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    for caturl, img, name, count in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + count.strip() + '][/COLOR]'
        site.add_dir(name, site.url[:-1] + caturl, 'List', img, name)
    np = re.compile(r'pagination_item--next.*?href="([^"]*?(\d+)[^"]*)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        site.add_dir('Next Page... ({0})'.format(nextpage), nplink, 'Categories', site.img_next)

    utils.eod()


@site.register()
def Pornstars(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="celebrities__celebrity[^"]*"[^>]*>'
        r'.*?href="([^"]+)"'                 
        r'.*?src="([^"]+)"'            
        r'.*?<h3[^>]*>([^<]+)</h3>'          
        r'.*?>([\d,]+)\s*videos'           
        , re.DOTALL | re.IGNORECASE
    )
    matches = pattern.findall(listhtml)
    for caturl, img, name, count in matches:
        name = utils.cleantext(name) + ' [COLOR yellow][' + count.strip() + '][/COLOR]'
        site.add_dir(name, site.url[:-1] + caturl, 'List', img, name)
    np = re.compile(r'pagination_item--next.*?href="([^"]*?(\d+)[^"]*)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        site.add_dir('Next Page... ({0})'.format(nextpage), nplink, 'Pornstars', site.img_next)

    utils.eod()

@site.register()
def PornSeries(url):
    listhtml = utils.getHtml(url)
    pattern = re.compile(
        r'class="thumb-serie .+?\s* href="([^"]+)".*?'                           
        r'data-src="([^"]+)".*?'                                                        
        r'<a[^>]*class="thumb-serie__name"[^>]*>(.*?)</a>'                    
        , re.DOTALL | re.IGNORECASE | re.MULTILINE
    )
    matches = pattern.findall(listhtml)
    for videopage, img, name in matches:
        name = utils.cleantext(name)
        videopage = site.url[:-1] + videopage
        site.add_dir(name, videopage, 'List', img, name)

    np = re.compile(r'pagination_item--next.*?href="([^"]*?(\d+)[^"]*)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if np:
        nplink = np.group(1) if np.group(1).startswith('http') else site.url[:-1] + np.group(1)
        nextpage = np.group(2)
        site.add_dir('Next Page... ({0})'.format(nextpage), nplink, 'PornSeries', site.img_next)
    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.play_from_site_link(url, url)
