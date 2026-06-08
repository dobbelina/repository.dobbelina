import os
import importlib
import xbmc

__all__ = []

_pkg = __name__  # 'resources.lib.sites'
_dir = os.path.dirname(__file__)

for _filename in os.listdir(_dir):
    if _filename.startswith('__') or not _filename.endswith('.py'):
        continue
    _module_name = _filename[:-3]
    try:
        importlib.import_module('{0}.{1}'.format(_pkg, _module_name))
        __all__.append(_module_name)
    except Exception as e:
        xbmc.log('"@@@@Cumination: Incompatible site ({0}): {1}'.format(_module_name, e), xbmc.LOGERROR)
