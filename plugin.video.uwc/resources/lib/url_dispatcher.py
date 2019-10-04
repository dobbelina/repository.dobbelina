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


class URL_Dispatcher:
    def __init__(self):
        self.func_registry = {}
        self.args_registry = {}
        self.kwargs_registry = {}

    def register(self, mode, args=None, kwargs=None):
        """
        Decorator function to register a function as a plugin:// url endpoint

        mode: the mode value passed in the plugin:// url
        args: a list  of strings that are the positional arguments to expect
        kwargs: a list of strings that are the keyword arguments to expect

        * Positional argument must be in the order the function expect
        * kwargs can be in any order
        * kwargs without positional arguments are supported by passing in a kwargs but no args
        * If there are no arguments at all, just "mode" can be specified
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = []

        def decorator(f):
            if mode in self.func_registry:
                message = 'Error: %s already registered as %s' % (str(f), mode)
                raise Exception(message)

            self.func_registry[mode.strip()] = f
            self.args_registry[mode] = args
            self.kwargs_registry[mode] = kwargs

            return f
        return decorator

    def dispatch(self, mode, queries):
        """
        Dispatch function to execute function registered for the provided mode

        mode: the string that the function was associated with
        queries: a dictionary of the parameters to be passed to the called function
        """
        if mode not in self.func_registry:
            message = 'Error: Attempt to invoke unregistered mode |%s|' % (mode)
            raise Exception(message)

        args = []
        kwargs = {}
        unused_args = queries.copy()
        if self.args_registry[mode]:
            # positional arguments are all required
            for arg in self.args_registry[mode]:
                arg = arg.strip()
                if arg in queries:
                    args.append(self.__coerce(queries[arg]))
                    del unused_args[arg]
                else:
                    message = 'Error: mode |%s| requested argument |%s| but it was not provided.' % (mode, arg)
                    raise Exception(message)

        if self.kwargs_registry[mode]:
            # kwargs are optional
            for arg in self.kwargs_registry[mode]:
                arg = arg.strip()
                if arg in queries:
                    kwargs[arg] = self.__coerce(queries[arg])
                    del unused_args[arg]

        if 'mode' in unused_args: del unused_args['mode']  # delete mode last in case it's used by the target function
        if unused_args: pass
        self.func_registry[mode](*args, **kwargs)

    def showmodes(self):
        import xbmc
        for mode in sorted(self.func_registry, key=lambda x: int(x)):
            value = self.func_registry[mode]
            args = self.args_registry[mode]
            kwargs = self.kwargs_registry[mode]
            line = 'Mode %s Registered - %s args: %s kwargs: %s' %(str(mode), str(value), str(args), str(kwargs))
            xbmc.log(line, xbmc.LOGNOTICE)

    # since all params are passed as strings, do any conversions necessary to get good types (e.g. boolean)
    def __coerce(self, arg):
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
