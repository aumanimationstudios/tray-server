#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-


__author__ = "Shrinidhi Rao"
__license__ = "GPL"
__email__ = "shrinidhi666@gmail.com"

import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore, uic
import subprocess
import time
import appdirs
import signal
import debug
import psutil
import ConfigParser
import fcntl
import dbus.mainloop.pyqt5
import dbus

def receive_signal(signum, stack):
  quit()

signal.signal(signal.SIGTERM, receive_signal)
signal.signal(signal.SIGINT, receive_signal)
signal.signal(signal.SIGABRT, receive_signal)
signal.signal(signal.SIGHUP, receive_signal)




homeconfig = appdirs.user_config_dir("tray-server")
try:
  os.makedirs(homeconfig)
except:
  debug.warn(sys.exc_info())
filepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-1])
options_ui_file = os.path.join(filepath, "selectionBox.ui")
config_file = os.path.join(homeconfig,"tray-server.ini")
app_lock_file = "/tmp/tray-server-{0}.lock".format(os.environ['USER'])
app_icon = os.path.join(filepath,"paf.png")
pidgin_notity_icon = os.path.join(filepath,"pidgin.png")
config_parser = ConfigParser.ConfigParser()
options_dict = {}

def update_config(options_ui):
  if(os.path.exists(config_file)):
    config_parser.read(config_file)
    options_dict['per-app-framework'] = config_parser.getint("tray","per-app-framework")
    options_ui.checkBox_paf_enable.setCheckState(options_dict['per-app-framework'])
    options_dict['notify-app-changes'] = config_parser.getint("tray","notify-app-changes")
    options_ui.checkBox_paf_notify.setCheckState(options_dict['notify-app-changes'])
    options_dict['pidgin-notify'] = config_parser.getint("tray", "pidgin-notify")
    options_ui.checkBox_pidgin.setCheckState(options_dict['pidgin-notify'])
    return(True)
  else:
    debug.warn(sys.exc_info())
    debug.warn("using defaults")
    options_dict['per-app-framework'] = option_ui.checkBox_paf_enable.checkState()
    options_dict['notify-app-changes'] = option_ui.checkBox_paf_notify.checkState()
    options_dict['pidgin-notify'] = option_ui.checkBox_pidgin.checkState()
    return(False)


def write_config(option_ui):
  debug.info("writing config file - start")
  debug.info(option_ui.checkBox_paf_enable.checkState())
  options_dict['per-app-framework'] = option_ui.checkBox_paf_enable.checkState()
  options_dict['notify-app-changes'] = option_ui.checkBox_paf_notify.checkState()
  options_dict['pidgin-notify'] = option_ui.checkBox_pidgin.checkState()
  try:
    config_parser.add_section("tray")
  except:
    debug.warn(sys.exc_info())
  for x in options_dict.keys():
    if(x):
      config_parser.set("tray",x,options_dict[x])

  with open(config_file,"wb") as config_fd:
    config_parser.write(config_fd)
  debug.info("writing config file - done")



class pidginNotify(QtCore.QThread):
  msg_received = QtCore.pyqtSignal(object)

  def __init__(self):
    super(pidginNotify, self).__init__()
    self.dbus_loop = dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)

    self.bus = dbus.SessionBus(mainloop=self.dbus_loop)
    while(True):
      try:
        self.purple = self.bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
        break
      except:
        time.sleep(1)
        print(sys.exc_info())

    self.purple.connect_to_signal("ReceivedImMsg", self.receive_msg)
    self.purple.connect_to_signal("SendingImMsg", self.receive_msg)

  def receive_msg(self, *args):
    self.msg_received.emit(args)


class appChangedPoll(QtCore.QThread):
  app_changed = QtCore.pyqtSignal(str)

  def __init__(self):
    super(appChangedPoll,self).__init__()

  def run(self):
    active_window_cmd = "xprop -root"
    lastapp = ""
    while (True):
      p = subprocess.Popen(active_window_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].split("\n")
      for x in p:
        if (x.startswith("_NET_ACTIVE_WINDOW(WINDOW)")):
          window_name_cmd = "xprop -id {0}".format(x.split("#")[-1].strip())
          q = subprocess.Popen(window_name_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].split("\n")
          for y in q:
            if (y.startswith("WM_CLASS(STRING)")):
              if(lastapp != y):
                self.app_changed.emit(unicode(y).split("=")[-1].strip().split(",")[-1].strip().strip("\"").lower())
                lastapp = y
      time.sleep(1)

def main():
  app = QtWidgets.QApplication(sys.argv)
  changePoll = appChangedPoll()
  changePoll.start()
  pidgin = pidginNotify()
  pidgin.start()
  options_ui = uic.loadUi(options_ui_file)
  update_config(options_ui)
  options_ui.pushButton_ok.clicked.connect(lambda a, s = options_ui: hide_options_ui(s,a))
  options_ui.checkBox_paf_enable.clicked.connect(lambda a, s = options_ui: write_config(s))
  options_ui.checkBox_paf_notify.clicked.connect(lambda a, s=options_ui: write_config(s))
  options_ui.checkBox_pidgin.clicked.connect(lambda a, s=options_ui: write_config(s))
  trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(app_icon), app)
  trayIcon.activated.connect(lambda action, tray=trayIcon,ui=options_ui: action_triggered(action,tray,ui))
  menu = QtWidgets.QMenu()
  exitAction = menu.addAction("Exit")
  trayIcon.setContextMenu(menu)
  exitAction.triggered.connect(quit)
  trayIcon.setToolTip("tray-server")
  trayIcon.show()
  changePoll.app_changed.connect(lambda s, tray=trayIcon : run_per_app(tray, s))
  pidgin.msg_received.connect(lambda s, tray=trayIcon: notity_pidgin_received_msg(tray,s))
  app_lock(trayIcon)
  run_once()
  # sys.exit(app.exec_())
  os._exit((app.exec_()))



def app_lock(tray):
  import random
  time.sleep(random.uniform(0.000,0.500))
  if(os.path.exists(app_lock_file)):
    f = open(app_lock_file,"r")
    pid = f.read().strip()
    f.close()
    debug.info(pid)
    try:
      p = psutil.Process(int(pid))
      if(os.path.abspath(p.cmdline()[1]) == os.path.abspath(__file__)):
        tray.showMessage('tray-server', 'Already an instance of the app is running.',msecs = 10000)
        tray.showMessage('tray-server', 'Delete the file \'{0}\' if you want to force run it'.format(app_lock_file),msecs = 10000)
        debug.warning("already an instance of the app is running.")
        debug.warning("delete the file {0}".format(app_lock_file))
        QtCore.QCoreApplication.instance().quit()
        os._exit(1)
      else:
        raise Exception("seems like a different process has the same pid")
    except:
      debug.warn(sys.exc_info())
      f = open(app_lock_file,"w")
      try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
      except:
        debug.error(sys.exc_info())
        QtCore.QCoreApplication.instance().quit()
        os._exit(1)
      f.write(unicode(os.getpid()))
      f.flush()
      fcntl.flock(f, fcntl.LOCK_UN)
      f.close()
  else:
    f = open(app_lock_file,"w")
    try:
      fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
      debug.error(sys.exc_info())
      QtCore.QCoreApplication.instance().quit()
      os._exit(1)
    f.write(unicode(os.getpid()))
    f.flush()
    fcntl.flock(f, fcntl.LOCK_UN)
    f.close()


def hide_options_ui(options_ui,arg):
  write_config(options_ui)
  debug.info(arg)
  options_ui.hide()



def quit():
  debug.debug("quitting")
  try:
    os.remove(app_lock_file)
  except:
    debug.error(sys.exc_info())
  QtCore.QCoreApplication.instance().quit()
  os._exit(0)

def run_once():
  if(os.path.exists(os.path.join(homeconfig,"per-app-framework-default"))):
    try:
      p = subprocess.Popen(os.path.join(homeconfig,"per-app-framework-default"),shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE).communicate()[0]
      debug.info(p)
    except:
      debug.error(sys.exc_info())

def action_triggered(*args):
  debug.info(args[0])
  if(args[0] == QtWidgets.QSystemTrayIcon.Trigger):
    # args[-1].setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.X11BypassWindowManagerHint)
    args[-1].setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)

    # args[-1].setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    args[-1].show()
    # args[-1].setFocus()
    args[-1].setWindowTitle("tray-server")
    args[-1].move(QtGui.QCursor.pos() - QtCore.QPoint(0,args[-1].height()))
    update_config(args[-1])
    args[-1].raise_()

    # args[-1].

def messageClicked(*args):
  QtWidgets.QMessageBox.information(None,"tray-server","testing msgbox",QtWidgets.QMessageBox.Ok)
  debug.info(args)


def run_per_app(tray,appdets):
  debug.info(appdets)
  if (options_dict['notify-app-changes'] == QtCore.Qt.Checked):
    tray.showMessage("app-changed",appdets)
  if (options_dict['per-app-framework'] == QtCore.Qt.Checked):
    if(os.path.exists(os.path.join(homeconfig,appdets))):
      try:
        p = subprocess.Popen(os.path.join(homeconfig,appdets),shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE).communicate()[0]
        debug.info(p)
      except:
        debug.error(sys.exc_info())

def notity_pidgin_received_msg(tray,*args):
  debug.info(args)
  if(options_dict['pidgin-notify'] == QtCore.Qt.Checked):
    tray.showMessage(args[0][1].split("@")[0],args[0][2],msecs=1000*1000,icon=QtWidgets.QSystemTrayIcon.Information)
  # tray.messageClicked.connect(messageClicked)

if __name__ == '__main__':
  main()
