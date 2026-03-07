import pytest
from unittest.mock import MagicMock, patch
import os
import sys
from resources.lib import basics

class TestBasicsCoverage:
    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    def test_addImgLink(self, mock_listitem, mock_add_item):
        mock_add_item.return_value = True
        res = basics.addImgLink("Test Image", "http://image.com/img.jpg", "view_img")
        assert res == True
        assert mock_add_item.called
        # Check URL construction
        args, kwargs = mock_add_item.call_args
        assert "mode=view_img" in kwargs["url"]
        assert "url=http%3A%2F%2Fimage.com%2Fimg.jpg" in kwargs["url"]

    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    @patch("resources.lib.basics.addon.getSetting")
    def test_addDownLink_with_duration_and_desc(self, mock_get_setting, mock_listitem, mock_add_item):
        mock_get_setting.return_value = "false" # duration_in_name=false
        mock_add_item.return_value = True
        
        # Test with width/height to hit that branch
        basics.addDownLink("Video", "http://vid.com", "play", "http://icon.jpg", 
                           duration="10:00", desc="My description", quality="1080p")
        
        assert mock_add_item.called
        # Verify listitem interactions
        instance = mock_listitem.return_value
        assert instance.setInfo.called or instance.getVideoInfoTag.called

    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    @patch("resources.lib.basics.addon.getSetting")
    def test_addDownLink_posterfanart(self, mock_get_setting, mock_listitem, mock_add_item):
        mock_get_setting.return_value = "true" # posterfanart=true
        mock_add_item.return_value = True
        
        basics.addDownLink("Video", "http://vid.com", "play", "http://icon.jpg")
        
        instance = mock_listitem.return_value
        # Check setArt call
        args, kwargs = instance.setArt.call_args
        assert args[0]["fanart"] == "http://icon.jpg"

    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    @patch("resources.lib.basics.addon.getSetting")
    def test_addDownLink_del_fav(self, mock_get_setting, mock_listitem, mock_add_item):
        def side_effect(key):
            if key == "favorder": return "date added"
            return ""
        mock_get_setting.side_effect = side_effect
        mock_add_item.return_value = True
        
        # fav="del" triggers move to top/up/down logic
        basics.addDownLink("Download", "http://vid.com", "down", "http://icon.jpg", fav="del")
        
        instance = mock_listitem.return_value
        assert instance.addContextMenuItems.called
        # Check that we have multiple context menu items
        args, kwargs = instance.addContextMenuItems.call_args
        menu_items = args[0]
        assert len(menu_items) > 5

    @patch("resources.lib.basics.addon.getSetting")
    def test_eod_with_customview(self, mock_get_setting):
        mock_xbmc = sys.modules["xbmc"]
        mock_xbmcplugin = sys.modules["xbmcplugin"]
        with patch.object(mock_xbmc, "executebuiltin") as mock_exec, \
             patch.object(mock_xbmc, "getSkinDir", return_value="skin.estuary"), \
             patch.object(mock_xbmcplugin, "endOfDirectory") as mock_end:
            
            def side_effect(key):
                if key == "customview": return "true"
                if key == "setview": return "estuary;55"
                return ""
            mock_get_setting.side_effect = side_effect
            
            basics.eod()
            mock_exec.assert_called_with("Container.SetViewMode(55)")
            assert mock_end.called

    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    @patch("resources.lib.basics.addon.getSetting")
    def test_addDir_with_desc_and_fanart(self, mock_get_setting, mock_listitem, mock_add_item):
        mock_get_setting.return_value = "true" # posterfanart=true
        mock_add_item.return_value = True
        
        basics.addDir("Category", "http://site.com", "list", "http://icon.jpg", desc="Description")
        
        instance = mock_listitem.return_value
        assert instance.setArt.called
        args, kwargs = instance.setArt.call_args
        # With my fix in basics.py, this should now be iconimage
        assert args[0]["fanart"] == "http://icon.jpg"

    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    def test_addDir_basic(self, mock_listitem, mock_add_item):
        mock_add_item.return_value = True
        basics.addDir("Category", "http://site.com", "list", "http://icon.jpg")
        assert mock_add_item.called
        args, kwargs = mock_add_item.call_args
        assert kwargs["isFolder"] == True

    @patch("resources.lib.basics.xbmcplugin.addDirectoryItem")
    @patch("resources.lib.basics.xbmcgui.ListItem")
    def test_addDir_custom_list(self, mock_listitem, mock_add_item):
        mock_add_item.return_value = True
        basics.addDir("My List", "http://site.com", "list", "http://icon.jpg", 
                      listitem_id=123, custom_list=True)
        
        instance = mock_listitem.return_value
        assert instance.addContextMenuItems.called
        args, kwargs = instance.addContextMenuItems.call_args
        menu_items = args[0]
        assert any("Move item to ..." in item[0] for item in menu_items)
