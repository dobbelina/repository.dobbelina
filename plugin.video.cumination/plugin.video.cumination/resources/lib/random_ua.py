# Function from Resolveurl

# import xbmcaddon
import random
import time
import six
from resources.lib.basics import addon

# addon = xbmcaddon.Addon('script.module.resolveurl')
get_setting = addon.getSetting


def set_setting(id, value):
    if not isinstance(value, six.string_types):
        value = str(value)
    addon.setSetting(id, value)


BR_VERS = [
    ['%s.0' % i for i in range(80, 103)],
    ['75.0.3770.80', '76.0.3809.100', '78.0.3904.97', '79.0.3945.88', '80.0.3987.149',
     '81.0.4044.92', '83.0.4103.116', '84.0.4147.135', '86.0.4240.75', '90.0.4430.72',
     '91.0.4472.147', '101.0.0.0', '102.0.0.0', '106.0.0.0'],
    ['84.0.4147.135', '86.0.4240.75', '90.0.4430.72',
     '91.0.4472.147', '101.0.0.0', '102.0.0.0', '106.0.0.0']
]
WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2']
FEATURES = ['; WOW64', '; Win64; x64', '']
RAND_UAS = [
    'Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
    'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
    'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36 Edg/{br_ver}'
]


def get_ua():
    try:
        last_gen = int(get_setting('last_ua_create'))
    except:
        last_gen = 0
    if not get_setting('current_ua') or last_gen < (time.time() - (7 * 24 * 60 * 60)):
        index = random.randrange(len(RAND_UAS))
        versions = {'win_ver': random.choice(WIN_VERS), 'feature': random.choice(FEATURES), 'br_ver': random.choice(BR_VERS[index])}
        user_agent = RAND_UAS[index].format(**versions)
        set_setting('current_ua', user_agent)
        set_setting('last_ua_create', str(int(time.time())))
    else:
        user_agent = get_setting('current_ua')
    return user_agent
