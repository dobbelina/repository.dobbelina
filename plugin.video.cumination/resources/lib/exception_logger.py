# coding: utf-8
# (c) Roman Miroshnychenko <roman1972@gmail.com> 2020
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Exception logger with extended diagnostic info"""

import inspect
import sys
from contextlib import contextmanager
from platform import uname
from pprint import pformat
try:
    from typing import Text, Callable, Generator
except ImportError:
    pass

import xbmc

from resources.lib.utils import logger


def _format_vars(variables):
    # type: (dict) -> Text
    """
    Format variables dictionary

    :param variables: variables dict
    :return: formatted string with sorted ``var = val`` pairs
    """
    var_list = [(var, val) for var, val in variables.items()
                if not (var.startswith('__') or var.endswith('__'))]
    var_list.sort(key=lambda i: i[0])
    lines = []
    for var, val in var_list:
        lines.append('{} = {}'.format(var, pformat(val)))
    return '\n'.join(lines)


def _format_code_context(frame_info):
    # type: (tuple) -> Text
    context = ''
    if frame_info[4] is not None:
        for i, line in enumerate(frame_info[4], frame_info[2] - frame_info[5]):
            if i == frame_info[2]:
                context += '{}:>{}'.format(str(i).rjust(5), line)
            else:
                context += '{}: {}'.format(str(i).rjust(5), line)
    return context


FRAME_INFO_TEMPLATE = """File:
{file_path}:{lineno}
----------------------------------------------------------------------------------------------------
Code context:
{code_context}
----------------------------------------------------------------------------------------------------
Local variables:
{local_vars}
====================================================================================================
"""


def _format_frame_info(frame_info):
    # type: (tuple) -> Text
    return FRAME_INFO_TEMPLATE.format(
        file_path=frame_info[1],
        lineno=frame_info[2],
        code_context=_format_code_context(frame_info),
        local_vars=_format_vars(frame_info[0].f_locals)
    )


EXCEPTION_TEMPLATE = """
*********************************** Unhandled exception detected ***********************************
####################################################################################################
                                           Diagnostic info
----------------------------------------------------------------------------------------------------
Exception type  : {exc_type}
Exception value : {exc}
System info     : {system_info}
Python version  : {python_version}
Kodi version    : {kodi_version}
sys.argv        : {sys_argv}
----------------------------------------------------------------------------------------------------
sys.path:
{sys_path}
####################################################################################################
                                            Stack Trace
====================================================================================================
{stack_trace}
************************************* End of diagnostic info ***************************************
"""


@contextmanager
def log_exception(logger_func=logger.error):
    # type: (Callable[[Text], None]) -> Generator[None, None, None]
    """
    Diagnostic helper context manager

    It controls execution within its context and writes extended
    diagnostic info to the Kodi log if an unhandled exception
    happens within the context. The info includes the following items:

    - System info
    - Python version
    - Kodi version
    - Module path.
    - Stack trace including:
        * File path and line number where the exception happened
        * Code fragment where the exception has happened.
        * Local variables at the moment of the exception.

    After logging the diagnostic info the exception is re-raised.

    Example::

        with debug_exception():
            # Some risky code
            raise RuntimeError('Fatal error!')

    :param logger_func: logger function that accepts a single argument
        that is a log message.
    """
    try:
        yield
    except Exception as exc:
        stack_trace = ''
        for frame_info in inspect.trace(5):
            stack_trace += _format_frame_info(frame_info)
        message = EXCEPTION_TEMPLATE.format(
            exc_type=exc.__class__.__name__,
            exc=exc,
            system_info=uname(),
            python_version=sys.version.replace('\n', ' '),
            kodi_version=xbmc.getInfoLabel('System.BuildVersion'),
            sys_argv=pformat(sys.argv),
            sys_path=pformat(sys.path),
            stack_trace=stack_trace
        )
        logger_func(message)
        raise exc
