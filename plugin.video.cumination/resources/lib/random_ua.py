# Function from Resolveurl, edited for modern current browsers

import random
import time
import six
from resources.lib.basics import addon

get_setting = addon.getSetting


def set_setting(id, value):
    if not isinstance(value, six.string_types):
        value = str(value)
    addon.setSetting(id, value)


def generate_ua():
    BR_VERS = {
        'Firefox': ['%s.0' % i for i in range(120, 147)],
        'Chrome': ['%s.0.0.0' % i for i in range(120, 144)],
        'Edg': ['%s.0.0.0' % i for i in range(120, 144)]
    }
    WIN_VERS = ['Windows NT 10.0']
    FEATURES = ['; Win64; x64']
    RAND_UAS = [
        'Mozilla/5.0 ({os_ver}{feature}; rv:{br_ver}) Gecko/20100101 Firefox/{br_ver}',
        'Mozilla/5.0 ({os_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36',
        'Mozilla/5.0 ({os_ver}{feature}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{br_ver} Safari/537.36 Edg/{br_ver}'
    ]

    browser = random.choice(list(BR_VERS.keys()))
    os_ver = random.choice(WIN_VERS)
    feature = random.choice(FEATURES)
    br_ver = random.choice(BR_VERS[browser])

    user_agent_template = next((ua for ua in RAND_UAS if browser.lower() in ua.lower()), RAND_UAS[0])
    return user_agent_template.format(os_ver=os_ver, feature=feature, br_ver=br_ver)


def get_ua():
    try:
        last_gen = int(get_setting('last_ua_create'))
    except Exception:
        last_gen = 0
    if not get_setting('current_ua') or last_gen < (time.time() - (7 * 24 * 60 * 60)):
        user_agent = generate_ua()
        set_setting('current_ua', user_agent)
        set_setting('last_ua_create', str(int(time.time())))
    else:
        user_agent = get_setting('current_ua')
    return user_agent


def force_ua():
    return generate_ua()


def set_ua(ua):
    set_setting('current_ua', ua)
    set_setting('last_ua_create', str(int(time.time())))
