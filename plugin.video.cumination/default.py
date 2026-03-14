"""
Cumination
Copyright (C) 2016 Whitecream

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

import os.path
import sys
import socket
import importlib
import six

from kodi_six import xbmc, xbmcplugin, xbmcvfs

from resources.lib import basics
from resources.lib.url_dispatcher import URL_Dispatcher
from resources.lib import utils
from resources.lib import favorites
from resources.lib import pin
from resources.lib.adultsite import AdultSite
from resources.lib.sites import *  # noqa

socket.setdefaulttimeout(60)

addon = basics.addon
addon_get_setting = addon.getSetting
content = "movies" if addon_get_setting("content") == "0" else "videos"
xbmcplugin.setContent(basics.addon_handle, content)
TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath
progress = utils.progress
dialog = utils.dialog

url_dispatcher = URL_Dispatcher("main")

custom_site_import_results = {"loaded": [], "failed": []}


def _record_custom_site_result(result_type, module_name, **details):
    custom_site_import_results[result_type].append({"module": module_name, **details})


def _handle_custom_site_failure(module_name, error, dependency=None):
    error_kind = "dependency" if dependency else "site"
    title = favorites.get_custom_site_title_by_module(module_name)
    readable_title = title or module_name
    utils.kodilog(
        "Custom site import failed [{0}] {1}: {2}".format(
            error_kind, module_name, error
        ),
        xbmc.LOGERROR,
    )
    favorites.disable_custom_site_by_module(module_name)
    message_lines = [
        "[B]{0}[/B]".format(readable_title),
        utils.i18n("custom_msg"),
    ]
    if dependency:
        message_lines.append(
            "Missing dependency: [COLOR red]{0}[/COLOR]".format(dependency)
        )
    else:
        message_lines.append("Import error detected inside the site module.")
    message_lines.append(
        "The site has been disabled; reinstall or fix the issue to re-enable it."
    )
    utils.textBox(utils.i18n("disable_custom"), "[CR]".join(message_lines))
    _record_custom_site_result(
        "failed",
        module_name,
        title=title,
        error=str(error),
        dependency=dependency,
        error_kind=error_kind,
    )


def load_custom_sites():
    custom_site_import_results["loaded"].clear()
    custom_site_import_results["failed"].clear()
    if addon_get_setting("custom_sites") != "true":
        return custom_site_import_results

    if basics.customSitesDir not in sys.path:
        sys.path.append(basics.customSitesDir)
    for module_name in favorites.enabled_custom_sites():
        try:
            importlib.import_module(module_name)
        except ImportError as error:
            dependency = getattr(error, "name", None)
            missing_dependency = (
                dependency if dependency and dependency != module_name else None
            )
            _handle_custom_site_failure(
                module_name, error, dependency=missing_dependency
            )
        except Exception as error:
            _handle_custom_site_failure(module_name, error)
        else:
            _record_custom_site_result("loaded", module_name)
    return custom_site_import_results


load_custom_sites()


@url_dispatcher.register()
def custom_sites_health():
    enabled_sites = favorites.enabled_custom_sites()
    if not enabled_sites:
        utils.textBox("Custom site health", "No custom sites are enabled.")
        return

    loaded_sites_data = custom_site_import_results.get("loaded", [])
    failed_sites = custom_site_import_results.get("failed", [])
    loaded_modules = {site["module"] for site in loaded_sites_data}
    failed_modules = {failure["module"] for failure in failed_sites}
    message_lines = []

    if loaded_modules:
        message_lines.append("[B]Loaded custom sites[/B]")
        for module_name in sorted(loaded_modules):
            title = (
                favorites.get_custom_site_title_by_module(module_name) or module_name
            )
            message_lines.append("• {0}".format(title))

    if failed_sites:
        message_lines.append("[B]Failed to load[/B]")
        for failure in sorted(failed_sites, key=lambda x: x["module"]):
            title = failure.get("title") or favorites.get_custom_site_title_by_module(
                failure["module"]
            )
            descriptor = (
                failure["dependency"] if failure.get("dependency") else "import error"
            )
            message_lines.append(
                "• {0} ({1})".format(title or failure["module"], descriptor)
            )

    untouched = sorted(
        [
            m
            for m in enabled_sites
            if m not in loaded_modules and m not in failed_modules
        ]
    )
    if untouched:
        message_lines.append("[B]Not attempted[/B]")
        for module_name in untouched:
            title = (
                favorites.get_custom_site_title_by_module(module_name) or module_name
            )
            message_lines.append("• {0}".format(title))

    if not message_lines:
        message_lines.append("No custom site import activity recorded.")

    utils.textBox("Custom site health", "[CR]".join(message_lines))


@url_dispatcher.register()
def INDEX():
    url_dispatcher.add_dir(
        "[COLOR white]{}[/COLOR]".format(utils.i18n("sites")),
        "",
        "site_list",
        basics.cum_image("cum-sites.png"),
        "",
        list_avail=False,
    )
    if any(AdultSite.get_testing_sites()):
        url_dispatcher.add_dir(
            "[COLOR white]Testing Sites[/COLOR]",
            "",
            "testing_site_list",
            basics.cum_image("cum-sites.png"),
            "",
            list_avail=False,
        )
    url_dispatcher.add_dir(
        "[COLOR white]{}[/COLOR]".format(utils.i18n("fav_videos")),
        "1",
        "favorites.List",
        basics.cum_image("cum-fav.png"),
        "",
        list_avail=False,
    )
    download_path = addon_get_setting("download_path")
    if download_path != "" and xbmcvfs.exists(download_path):
        url_dispatcher.add_dir(
            "[COLOR white]{}[/COLOR]".format(utils.i18n("dnld_folder")),
            download_path,
            "OpenDownloadFolder",
            basics.cum_image("cum-downloads.png"),
            "",
            list_avail=False,
        )

    url_dispatcher.add_dir(
        "[COLOR white]{}[/COLOR]".format(utils.i18n("custom_list")),
        "",
        "favorites.create_custom_list",
        Folder=False,
        list_avail=False,
    )
    if addon_get_setting("custom_sites") == "true":
        url_dispatcher.add_dir(
            "[COLOR white]Custom site health[/COLOR]",
            "",
            "custom_sites_health",
            basics.cum_image("cum-sites.png"),
            "",
            list_avail=False,
        )
    for rowid, name in favorites.get_custom_lists():
        url_dispatcher.add_dir(
            name,
            str(rowid),
            "favorites.load_custom_list",
            list_avail=False,
            custom_list=True,
        )
    favorites.load_custom_list("main")
    url_dispatcher.add_dir(
        "[COLOR white]{}[/COLOR]".format(utils.i18n("clear_cache")),
        "",
        "utils.clear_cache",
        basics.cuminationicon,
        "",
        Folder=False,
        list_avail=False,
    )

    utils.eod(basics.addon_handle, False)


@url_dispatcher.register()
def site_list():
    custom_listitems = favorites.get_custom_listitems()
    custom_listitems_dict = {}
    for x in custom_listitems:
        custom_listitems_dict[x[0]] = x[1]
    for x in sorted(
        AdultSite.get_sites(), key=lambda y: y.get_clean_title().lower(), reverse=False
    ):
        if x.custom:
            utils.kodilog(
                "{0}: {1}".format(utils.i18n("list_custom"), x.title), xbmc.LOGDEBUG
            )
        title = x.title
        if title in custom_listitems_dict:
            title = "{} [COLOR red]{}[/COLOR]".format(
                title, "".ljust(custom_listitems_dict[title], "*")
            )
        url_dispatcher.add_dir(
            title, x.url, x.default_mode, x.image, about=x.about, custom=x.custom
        )
    utils.eod(basics.addon_handle, False)


@url_dispatcher.register()
def testing_site_list():
    for x in sorted(
        AdultSite.get_testing_sites(),
        key=lambda y: y.get_clean_title().lower(),
        reverse=False,
    ):
        url_dispatcher.add_dir(
            "[COLOR gold][TEST][/COLOR] {}".format(x.title),
            x.url,
            x.default_mode,
            x.image,
            about=x.about,
            custom=x.custom,
        )
    utils.eod(basics.addon_handle, False)


@url_dispatcher.register()
def OpenDownloadFolder(url):
    xbmc.executebuiltin("Dialog.Close(busydialog, true)")
    xbmc.sleep(100)
    xbmc.executebuiltin("ActivateWindow(Videos, " + url + ")")


@url_dispatcher.register()
def smrSettings():
    import resolveurl

    resolveurl.display_settings()


@url_dispatcher.register()
def openLogUploader():
    from resources.lib.jsonrpc import check_addon

    if check_addon("script.kodi.loguploader"):
        xbmc.executebuiltin("RunScript(script.kodi.loguploader)")
    else:
        dialog.ok(
            "Kodi Logfile Uploader",
            "Installing Kodi Logfile Uploader unsuccesful\nPlease install it manually from the Kodi repository",
        )


@url_dispatcher.register()
def about_site(name, about, custom):
    heading = "{0} {1}".format(utils.i18n("about"), name)
    dir = basics.customSitesDir if custom else basics.aboutDir
    with open(TRANSLATEPATH(os.path.join(dir, "{}.txt".format(about)))) as f:
        announce = f.read()
    utils.textBox(heading, announce)


def change():
    version = addon.getAddonInfo("version")
    if addon_get_setting("changelog_seen_version") == version or not os.path.isfile(
        basics.changelog
    ):
        return
    addon.setSetting("changelog_seen_version", version)
    heading = "[B][COLOR hotpink]Cumination[/COLOR] [COLOR white]Changelog[/COLOR][/B]"
    with open(basics.changelog) as f:
        cl_lines = f.readlines()
    announce = ""
    for line in cl_lines:
        if not line.strip():
            break
        announce += line
    utils.textBox(heading, announce)


if not addon_get_setting("cuminationage") == "true":
    age = dialog.yesno(
        utils.i18n("warn"),
        utils.i18n("warn_msg"),
        nolabel=utils.i18n("exit"),
        yeslabel=utils.i18n("enter"),
    )
    if age:
        addon.setSetting("cuminationage", "true")
else:
    age = True


def process_queries(argv):
    if sys.argv:
        argv = sys.argv
    queries = utils.parse_query(argv[2])
    mode = queries.get("mode", None)
    widget = bool(queries.get("widget", ""))
    if widget:
        ins = AdultSite.get_site_by_name(mode.split(".")[0])
        ins.widget = True
    url_dispatcher.dispatch(mode, queries)


def main(argv=None):
    if addon_get_setting("enh_debug") == "true":
        from resources.lib import exception_logger

        with exception_logger.log_exception():
            process_queries(argv)
    else:
        process_queries(argv)


if __name__ == "__main__":
    if pin.CheckPin():
        if age:
            change()
            sys.exit(main())
