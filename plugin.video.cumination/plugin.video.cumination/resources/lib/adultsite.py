from resources.lib.url_dispatcher import URL_Dispatcher
from weakref import WeakSet
import re
from resources.lib import basics


class AdultSite(URL_Dispatcher):
    instances = WeakSet()
    clean_functions = set()

    def __init__(self, name, title, url, image=None, about=None, webcam=False):
        self.default_mode = ''
        self.name = name
        self.title = title + '[COLOR white] - webcams[/COLOR]' if webcam else title
        self.url = url
        self.image = basics.cum_image(image) if image else ''
        self.about = about
        self.webcam = webcam
        self.custom = False
        self.add_to_instances()

    def add_to_instances(self):
        super(AdultSite, self).__init__(self.name)
        self.__class__.instances.add(self)

    def get_clean_title(self):
        title = self.title
        if ']' in title and '[/' in title:
            title = ''.join(re.compile(r'[\]](.*?)[\[]/').findall(title))
        return title

    def register(self, default_mode=False, clean_mode=False):
        def dec(f):
            if default_mode:
                if self.default_mode:
                    raise Exception('A default mode is already defined')
                self.default_mode = '{}.{}'.format(self.module_name, f.__name__)
            if clean_mode:
                self.__class__.clean_functions.add(f)
            super_register = super(AdultSite, self).register()
            func = super_register(f)
            return func
        return dec

    @classmethod
    def get_sites(cls):
        for ins in cls.instances:
            if ins.default_mode:
                yield ins

    @classmethod
    def get_internal_sites(cls):
        for ins in cls.instances:
            if ins.default_mode and not ins.custom:
                yield ins

    @classmethod
    def get_site_by_name(cls, name):
        for ins in cls.instances:
            if ins.name == name and ins.default_mode:
                return ins
        return None

    @classmethod
    def get_sites_by_name(cls, names):
        for name in names:
            site = cls.get_site_by_name(name)
            if site:
                yield site

    @classmethod
    def get_custom_sites(cls):
        for ins in cls.instances:
            if ins.default_mode and ins.custom:
                yield ins
