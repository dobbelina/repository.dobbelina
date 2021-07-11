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
    ['%s.0' % i for i in range(60, 90)],
    ['48.0.2564.109', '49.0.2623.75', '50.0.2661.75', '51.0.2704.84', '53.0.2785.116', '54.0.2840.71', '55.0.2883.75', '56.0.2924.87',
     '57.0.2987.133', '58.0.3029.96', '59.0.3071.86', '60.0.3112.78', '61.0.3163.79', '62.0.3202.75', '63.0.3239.108', '64.0.3282.140',
     '65.0.3325.181', '66.0.3359.181', '67.0.3396.79', '68.0.3440.84', '69.0.3497.92', '70.0.3538.77', '71.0.3578.80', '75.0.3770.80',
     '76.0.3809.100', '78.0.3904.97', '79.0.3945.88', '80.0.3987.149', '81.0.4044.92', '83.0.4103.116', '84.0.4147.135', '86.0.4240.75',
     '90.0.4430.72', '91.0.4472.147'],
    ['11.0'],
    ['10.0', '10.6']]
WIN_VERS = ['Windows NT 10.0', 'Windows NT 7.0', 'Windows NT 6.3', 'Windows NT 6.2']  # , 'Windows NT 6.1', 'Windows NT 6.0', 'Windows NT 5.1', 'Windows NT 5.0']
FEATURES = ['; WOW64', '; Win64; x64', '']
RAND_UAS = ['Mozilla/5.0 ({win_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
            'Mozilla/5.0 ({win_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
            'Mozilla/5.0 ({win_ver}{feature}; Trident/7.0; rv:{br_ver}) like Gecko',
            'Mozilla/5.0 (compatible; MSIE {br_ver}; {win_ver}{feature}; Trident/6.0)']


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
