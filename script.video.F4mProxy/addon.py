import xbmc, xbmcgui
 
#get actioncodes from https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/Key.h
ACTION_PREVIOUS_MENU = 10
ACTION_SELECT_ITEM = 7
 
class MyClass(xbmcgui.Window):
  def __init__(self):
    self.strActionInfo = xbmcgui.ControlLabel(100, 120, 800, 400, '', 'font13', '0xFFFF00FF')
    self.addControl(self.strActionInfo)
    self.strActionInfo.setLabel('More options here to control the f4m Proxy, please any key to close')
 
  def onAction(self, action):
      self.close()
 
  def message(self, message):
    dialog = xbmcgui.Dialog()
    dialog.ok("Byebye!", message)
 
mydisplay = MyClass()
mydisplay .doModal()
del mydisplay