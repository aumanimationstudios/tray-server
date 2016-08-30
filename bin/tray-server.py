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

homeconfig = appdirs.user_config_dir("per-app-framework")
filepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-1])

class appChangedPoll(QtCore.QThread):
  appChanged = QtCore.pyqtSignal(str)

  def __init__(self):
    super(appChangedPoll,self).__init__()

  def run(self):
    active_window_cmd = "xprop -root"
    lastapp = ""
    while (True):
      p = subprocess.Popen(active_window_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[
        0].split("\n")
      for x in p:
        if (x.startswith("_NET_ACTIVE_WINDOW(WINDOW)")):
          window_name_cmd = "xprop -id {0}".format(x.split("#")[-1].strip())
          q = subprocess.Popen(window_name_cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()[0].split("\n")
          for y in q:
            if (y.startswith("WM_CLASS(STRING)")):
              if(lastapp != y):
                self.appChanged.emit(unicode(y).split("=")[-1].strip().split(",")[-1].strip().strip("\""))
                lastapp = y
      time.sleep(1)


def main():
  changePoll = appChangedPoll()
  changePoll.start()
  app = QtWidgets.QApplication(sys.argv)
  print(os.path.join(filepath,"paf.png"))

  trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(os.path.join(filepath,"paf.png")), app)
  menu = QtWidgets.QMenu()
  exitAction = menu.addAction("Exit")

  trayIcon.setContextMenu(menu)
  exitAction.triggered.connect(quit)
  trayIcon.show()
  changePoll.appChanged.connect(lambda s,tray=trayIcon : notify(tray,s))
  sys.exit(app.exec_())



def quit():
  QtCore.QCoreApplication.instance().quit()


def notify(tray,appdets):
  # tray.showMessage('App Changed', appdets,msecs = 3000)
  if(os.path.exists(os.path.join(homeconfig,appdets))):
    p = subprocess.Popen(os.path.join(homeconfig,appdets),shell=True,stderr=subprocess.PIPE,stdout=subprocess.PIPE).communicate()[0]
    print(p)


if __name__ == '__main__':
  main()
