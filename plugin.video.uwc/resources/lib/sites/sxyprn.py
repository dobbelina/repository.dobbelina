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

import re
import xbmc
import xbmcplugin
import xbmcgui
from resources.lib import utils

BASE_URL = 'https://sxyprn.com'


def make_url(link):
    return link if link.startswith('http') else 'https:' + link if link.startswith('//') else BASE_URL + link


@utils.url_dispatcher.register('650')
def yourporn_main():
    utils.addDir('[COLOR hotpink]Categories[/COLOR]','https://sxyprn.com/', 653, '', '')
    utils.addDir('[COLOR hotpink]Top networks[/COLOR]','https://sxyprn.com/', 654, '', '', section='networks')
    utils.addDir('[COLOR hotpink]Top pornstars[/COLOR]','https://sxyprn.com/', 654, '', '', section='pornstars')
    utils.addDir('[COLOR hotpink]Top rated last week[/COLOR]','https://sxyprn.com/popular/top-rated.html', 651, '', section='rating')
    utils.addDir('[COLOR hotpink]Top viewed last week[/COLOR]','https://sxyprn.com/popular/top-viewed.html', 651, '', section='views')
    utils.addDir('[COLOR hotpink]Orgasmic[/COLOR]','https://sxyprn.com/orgasm/', 651, '', section='orgasmic')
    utils.addDir('[COLOR hotpink]Search[/COLOR]','https://sxyprn.com/', 655, '', '')
    yourporn_list('https://sxyprn.com/blog/all/0.html?fl=all&sm=latest')



@utils.url_dispatcher.register('651', ['url', 'page'], ['section'])
def yourporn_list(url, page=None, section=None):
    listhtml = utils.getHtml(url)
    
    if '>Nothing Found. See More...<' in listhtml: 
        utils.notify('SEARCH','Nothing Found.')
        return

    videos = listhtml.split("div class='post_el_small'")
    
    for video in videos:
        match = re.compile("href='([^']+)' title='([^']+)'>", re.DOTALL | re.IGNORECASE).findall(video)
        if match:
            (videourl, title) = match[0]
            name = title
            if "img class='mini_post_vid_thumb'" in video:
                img = re.compile("src='(//[^']+jpg)'", re.DOTALL | re.IGNORECASE).findall(video)
                if img:
                    img = 'https:' + img[0]
                else:
                    img = ''
            else:
                img = ''
                
            if "class='duration_small'" in video:
                duration = re.compile(">([\d\?:]+)<", re.DOTALL | re.IGNORECASE).findall(video)[0]
            else:
                duration = ''

            if '#' in name:
                name = name.split('#')[0]
                name = name.replace('\t',' ')
                name = name.replace('\n',' ')

            if "title='bitrate" in video:
                match_hd = re.compile("'bitrate[^']+'>([^<]+)<", re.DOTALL | re.IGNORECASE).findall(video)
                hd = " [COLOR orange]" + match_hd[0] + "[/COLOR]"
            else:
                hd = ''
            if duration == '??':
                duration = 'Prepairing new video. Please wait'
                
            if 'http://' in title or 'https://' in title:
                videourls = re.compile("(http.+?)(?:\s|'|$)", re.DOTALL | re.IGNORECASE).findall(title)
                videourl = '|'.join(videourls) + '@'
                duration = 'EXTERNAL LINK'

            name = utils.cleantext(name) + hd + " [COLOR deeppink]" + duration + "[/COLOR]"
            img = make_url(img)
            videourl = make_url(videourl)
        
            utils.addDownLink(name, videourl, 652, img, '')            
    try:
        next_page = re.compile("<a href='([^']+)' class='tdn'><div class='next", re.DOTALL | re.IGNORECASE).search(listhtml).group(1)
        next_page = make_url(next_page)
        utils.addDir('Next Page' , next_page, 651, '')
    except:
        pass
    
    if 'popular' in url or 'orgasm' in url:
        m = re.search('/(\d+)$', url)
        if m:
            page = m.group(1)
            nextp = str(int(page) + 30)
            next_page = url.replace('/'+page,'/'+nextp )
        else:
            if url.endswith('/'):
                next_page = url + '30'
            else:
                next_page = url + '/' + '30'
        utils.addDir('Next Page' , next_page, 651, '')
    
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('653', ['url'])
def yourporn_cat(url):
    listhtml = utils.getHtml(url)
    listhtml=listhtml.replace("\'",'"')
    match = re.compile('<a href="([^"]+)" target="_blank"><div class="top_sub_el top_sub_el_sc"><span class="top_sub_el_key_sc">([^<]+)</span><span class="top_sub_el_count">([^<]+)</span></div>', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for catpage, name, count in match: #sorted(match, key=lambda x: x[2]):
        name = name.strip() + " [COLOR deeppink]" + count + "[/COLOR]"
        utils.addDir(name, make_url(catpage) + '?sm=latest', 651, '', 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('654', ['url'], ['section'])
def yourporn_channels(url, section):
    listhtml = utils.getHtml(url)
    if section == 'networks':
        handle = 'sc'
        categories = re.compile('''<span>Top SubCat Subs</span>(.*?)<div class='splitter_block_header'>''', re.DOTALL | re.IGNORECASE).search(listhtml).group(1)
    else:
        handle = 'ps'
        categories = re.compile('''<span>Top PornStars Subs</span>(.*?)<span>Top SubCat Subs</span>''', re.DOTALL | re.IGNORECASE).search(listhtml).group(1)

    match = re.compile("<a href='([^']+)'.*?<span class='top_sub_el_key_" + handle + "'>([^<]+)<.*?<span class='top_sub_el_count'>([^<]+)<", re.DOTALL | re.IGNORECASE).findall(categories)
    for catpage, name, count in sorted(match, key=lambda x: x[1]):
        name = name  + " [COLOR deeppink]" + count + "[/COLOR]"
        utils.addDir(name, make_url(catpage), 651, '', 1)
    xbmcplugin.endOfDirectory(utils.addon_handle)


@utils.url_dispatcher.register('655', ['url'], ['keyword'])
def yourporn_search(url, keyword=None):
    if not keyword:
        utils.searchDir(url, 655)
    else:
        title = keyword.replace(' ','_')
        url = url + title + '.html'
        yourporn_list(url)


def ssut51(str):
    str = re.sub(r'\D', '', str)
    sut = 0
    for i in range(0, len(str)):
        sut += int(str[i])
    return sut

@utils.url_dispatcher.register('652', ['url', 'name'], ['download'])
def yourporn_play(url, name, download=None):

    vp = utils.VideoPlayer(name, download = download)
    vp.progress.update(25, "", "Playing video", "")        
    if url.endswith('@'):
        urls = url[:-1]
        urls = urls.split('|')
        vp.play_from_link_list(urls)
    else:
        url = url.replace('https://yps.to/','https://sxyprn.com/')
        html = utils.getHtml(url, '')
        html0 = html.split("class='comments_blog")[0]
        if "title='>External Link!<'" in html0:
            vp.play_from_html(html0)
        else:
            videourl = re.compile('''data-vnfo='{".+?":"(.+?)"''', re.DOTALL | re.IGNORECASE).findall(html)[0].replace('\/','/')
            tmp = videourl.split('/')
            tmp[5] = str(int(tmp[5]) - ssut51(re.sub(r'\D', '', tmp[6])) - ssut51(re.sub(r'\D', '', tmp[7])))
            videourl = '/'.join(tmp)
            match = re.search('src="(/js/main[^"]+)"', html, re.DOTALL | re.IGNORECASE)
            if match:
                result = match.group(1)
                jsscript = utils.getHtml(make_url(result), url)
                replaceint = re.search(r'tmp\[1\]\+= "(\d+)";', jsscript, re.DOTALL | re.IGNORECASE).group(1)
                videourl = videourl.replace('/cdn/', '/cdn%s/' % replaceint)
            else:
                videourl = videourl.replace('/cdn/','/cdn8/')
            videourl = make_url(videourl)
            vp.progress.update(75, "", "Playing video", "")        
            vp.play_from_direct_link(videourl)


def yourporn_multiple_videos(html):
    videos = re.compile('''class="pl_vid_el transition".*?data-hash="([^"]+)".*?title="([^"]+)"''', re.DOTALL | re.IGNORECASE).findall(html)
    vids = {}
    for vid_hash, title in videos:
        vids[title] = vid_hash
    sel_vid_hash = utils.selector('Multiple videos found', vids, dont_ask_valid=False, sort_by=lambda x: x)
    if sel_vid_hash:
        vid_url = BASE_URL + "/post/" + sel_vid_hash + '.html'
        return utils.getHtml(vid_url)
    return None
