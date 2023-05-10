# -*- coding: utf-8 -*-

import re
import base64
from resources.lib import utils


def Tdecode(vidurl):
    replacemap = {'M': r'\u041c', 'A': r'\u0410', 'B': r'\u0412', 'C': r'\u0421', 'E': r'\u0415', '=': '~', '+': '.', '/': ','}

    for key in replacemap:
        vidurl = vidurl.replace(replacemap[key], key)
    vidurl = base64.b64decode(vidurl)
    return vidurl.decode('utf-8')


def GetTxxxVideo(vidpage):
    vidpagecontent = utils.getHtml(vidpage)
    posturl = 'https://%s/sn4diyux.php' % vidpage.split('/')[2]

    pC3 = re.search('''pC3:'([^']+)''', vidpagecontent).group(1)
    vidid = re.search(r'''video_id["|']?:\s*(\d+)''', vidpagecontent).group(1)
    data = '%s,%s' % (vidid, pC3)
    vidcontent = utils.getHtml(posturl, referer=vidpage, data={'param': data})
    vidurl = re.search('video_url":"([^"]+)', vidcontent).group(1)
    vidurl = Tdecode(vidurl)

    return vidurl + "|Referer=" + vidpage
