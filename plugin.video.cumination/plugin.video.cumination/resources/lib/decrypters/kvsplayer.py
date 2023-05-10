"""
@author: gujal and Cumination
"""


def kvs_decode(vu, lc, hr='16'):
    import time

    def calcseed(lc, hr):
        f = lc.replace('$', '').replace('0', '1')
        j = int(len(f) / 2)
        k = int(f[0:j + 1])
        el = int(f[j:])
        fi = abs(el - k) * 4
        s = str(fi)
        i = int(int(hr) / 2) + 2
        m = ''
        for g2 in range(j + 1):
            for h in range(1, 5):
                n = int(lc[g2 + h]) + int(s[g2])
                if n >= i:
                    n -= i
                m += str(n)
        return m

    if vu.startswith('function/'):
        vup = vu.split('/')
        uhash = vup[7][0: 2 * int(hr)]
        nchash = vup[7][2 * int(hr):]
        seed = calcseed(lc, hr)
        if seed and uhash:
            for k in range(len(uhash) - 1, -1, -1):
                el = k
                for m in range(k, len(seed)):
                    el += int(seed[m])
                while el >= len(uhash):
                    el -= len(uhash)
                n = ''
                for o in range(len(uhash)):
                    n += uhash[el] if o == k else uhash[k] if o == el else uhash[o]
                uhash = n
            vup[7] = uhash + nchash
        vu = '/'.join(vup[2:]) + '&rnd={}'.format(int(time.time() * 1000))
    return vu
