"""
    tknorris shared module
    Copyright (C) 2016 tknorris

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
"""

try:
    from inspect import getargspec
except ImportError:
    from inspect import getfullargspec as getargspec
from resources.lib.basics import addDir, addDownLink, addImgLink, searchDir, cum_image


class URL_Dispatcher(object):
    func_registry = {}
    args_registry = {}
    kwargs_registry = {}

    def __init__(self, module_name):
        if not module_name:
            message = 'Error: a module name is required'
            raise Exception(message)
        elif '.' in module_name:
            message = 'Error: module name cannot contain . character'
            raise Exception(message)

        self.module_name = module_name
        self.img_search = cum_image('cum-search.png')
        self.img_cat = cum_image('cum-cat.png')
        self.img_next = cum_image('cum-next.png')

    def get_full_mode(self, mode):
        return mode if '.' in str(mode) else '{}.{}'.format(self.module_name, mode)

    def register(self):

        def decorator(f):
            mode = '{}.{}'.format(self.module_name, f.__name__)
            all_args = getargspec(f)
            func_args = all_args.args[0:-len(all_args.defaults)] if all_args.defaults else all_args.args
            func_kwargs = all_args.args[len(func_args):] if all_args.defaults else []

            if mode in self.__class__.func_registry:
                message = 'Error: {} already registered as {}'.format(f, mode)
                raise Exception(message)

            self.__class__.func_registry[mode.strip()] = f
            self.__class__.args_registry[mode] = func_args
            self.__class__.kwargs_registry[mode] = func_kwargs

            return f
        return decorator

    def add_dir(self, name, url, mode, iconimage=None, page=None, channel=None, section=None, keyword='', Folder=True,
                about=None, custom=False, list_avail=True, listitem_id=None, custom_list=False, contextm=None, desc=''):
        mode = self.get_full_mode(mode)
        addDir(name, url, mode, iconimage, page, channel, section, keyword, Folder, about,
               custom, list_avail, listitem_id, custom_list, contextm, desc)

    def add_download_link(self, name, url, mode, iconimage, desc='', stream=None, fav='add', noDownload=False, contextm=None, fanart=None, duration='', quality=''):
        mode = self.get_full_mode(mode)
        addDownLink(name, url, mode, iconimage, desc, stream, fav, noDownload, contextm, fanart, duration, quality)

    def add_img_link(self, name, url, mode):
        mode = self.get_full_mode(mode)
        addImgLink(name, url, mode)

    def search_dir(self, url, mode, page=None):
        mode = self.get_full_mode(mode)
        searchDir(url, mode, page)

    @classmethod
    def dispatch(cls, mode, queries):
        """
        Dispatch function to execute function registered for the provided mode

        mode: the string that the function was associated with
        queries: a dictionary of the parameters to be passed to the called function
        """
        if mode not in cls.func_registry:
            message = 'Error: Attempt to invoke unregistered mode {}'.format(mode)
            raise Exception(message)

        args = []
        kwargs = {}
        unused_args = queries.copy()
        if cls.args_registry[mode]:
            # positional arguments are all required
            for arg in cls.args_registry[mode]:
                arg = arg.strip()
                if arg in queries:
                    args.append(cls.__coerce(queries[arg]))
                    del unused_args[arg]
                else:
                    message = 'Error: mode {} requested argument {} but it was not provided.'.format(mode, arg)
                    raise Exception(message)

        if cls.kwargs_registry[mode]:
            # kwargs are optional
            for arg in cls.kwargs_registry[mode]:
                arg = arg.strip()
                if arg in queries:
                    kwargs[arg] = cls.__coerce(queries[arg])
                    del unused_args[arg]

        if 'mode' in unused_args:
            del unused_args['mode']  # delete mode last in case it's used by the target function
        if unused_args:
            pass
        cls.func_registry[mode](*args, **kwargs)

    # since all params are passed as strings, do any conversions necessary to get good types (e.g. boolean)
    @staticmethod
    def __coerce(arg):
        try:
            temp = arg.lower()
            if temp == 'true':
                return True
            elif temp == 'false':
                return False
            elif temp == 'none':
                return None
            return arg
        except:
            return arg
