from resources.lib import basics
from resources.lib import utils  # noQA
from resources.lib.adultsite import AdultSite
from resources.lib.favorites import get_custom_data


class CustomSite(AdultSite):
    def __init__(self, author, name, webcam=False):
        self.default_mode = ''
        self.custom_name = name
        self.name = 'custom_' + name + '_by_' + author
        self.custom = True
        self.author = author
        self.webcam = webcam
        self.db_loaded = False
        self.db_title = None
        self.db_image = None
        self.db_about = None
        self.db_url = None
        self.add_to_instances()

    def load_stored_data(self):
        data = get_custom_data(self.author, self.custom_name)
        self.db_title, self.db_image, self.db_about, self.db_url = data
        self.db_loaded = True

    def load_stored_data_if_needed(self):
        if not self.db_loaded:
            self.load_stored_data()

    @property
    def title(self):
        self.load_stored_data_if_needed()
        return self.db_title + '[COLOR white] - webcams[/COLOR]' if self.webcam else self.db_title

    @property
    def image(self):
        self.load_stored_data_if_needed()
        return basics.cum_image(self.db_image, True) if self.db_image else None

    @property
    def about(self):
        self.load_stored_data_if_needed()
        return self.db_about

    @property
    def url(self):
        self.load_stored_data_if_needed()
        return self.db_url
