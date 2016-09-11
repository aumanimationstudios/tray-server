#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-
__author__ = "Shrinidhi Rao"
__license__ = "GPL"
__email__ = "shrinidhi666@gmail.com"

import sys
import os
from PyQt5 import QtWidgets, QtGui, QtCore
import subprocess
import time
import appdirs
import signal
import debug
import psutil

homeconfig = appdirs.user_config_dir("per-app-framework")
filepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-1])
app_lock_file = "/tmp/per-app-framework-{0}.lock".format(os.environ['USER'])

def receive_signal(signum, stack):
  quit()

signal.signal(signal.SIGTERM, receive_signal)
signal.signal(signal.SIGINT, receive_signal)
signal.signal(signal.SIGABRT, receive_signal)
signal.signal(signal.SIGHUP, receive_signal)


class appChangedPoll(QtCore.QThread):
  appChanged = QtCore.pyqtSignal(str)

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
                self.appChanged.emit(unicode(y).split("=")[-1].strip().split(",")[-1].strip().strip("\"").lower())
                lastapp = y
      time.sleep(1)


def main():
  changePoll = appChangedPoll()
  changePoll.start()
  app = QtWidgets.QApplication(sys.argv)
  debug.info(os.path.join(filepath,"paf.png"))

  trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(os.path.join(filepath,"paf.png")), app)
  menu = QtWidgets.QMenu()
  exitAction = menu.addAction("Exit")

  trayIcon.setContextMenu(menu)
  exitAction.triggered.connect(quit)
  trayIcon.setToolTip("per-app-framework")
  trayIcon.show()
  changePoll.appChanged.connect(lambda s,tray=trayIcon : notify(tray,s))
  app_lock(trayIcon)
  run_once()
  # sys.exit(app.exec_())
  os._exit((app.exec_()))



def app_lock(tray):
  if(os.path.exists(app_lock_file)):
    f = open(app_lock_file,"r")
    pid = f.read().strip()
    f.close()
    debug.info(pid)
    try:
      p = psutil.Process(int(pid))
      tray.showMessage('per-app-framework', 'Already an instance of the app is running.',msecs = 10000)
      tray.showMessage('per-app-framework', 'Delete the file \'{0}\' if you want to force run it'.format(app_lock_file),msecs = 10000)
      debug.warning("already an instance of the app is running.")
      debug.warning("delete the file {0}".format(app_lock_file))
      QtCore.QCoreApplication.instance().quit()
      os._exit(1)
    except:
      debug.warn(sys.exc_info())
      f = open(app_lock_file,"w")
      f.write(unicode(os.getpid()))
      f.flush()
      f.close()
  else:
    f = open(app_lock_file,"w")
    f.write(unicode(os.getpid()))
    f.flush()
    f.close()




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


def notify(tray,appdets):
  debug.info(appdets)
  if(os.path.exists(os.path.join(homeconfig,appdets))):
    try:
      p = subprocess.Popen(os.path.join(homeconfig,appdets),shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE).communicate()[0]
      debug.info(p)
    except:
      debug.error(sys.exc_info())


if __name__ == '__main__':
  main()
