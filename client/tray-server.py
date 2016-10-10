#!/usr/bin/env python2.7
#-*- coding: utf-8 -*-
__author__ = "Shrinidhi Rao"
__license__ = "GPL"
__email__ = "shrinidhi666@gmail.com"

import ConfigParser
import fcntl
import os
import signal
import subprocess
import sys
import tempfile
import time

import appdirs
import dbus
import dbus.mainloop.pyqt5
import psutil
from PyQt5 import QtWidgets, QtGui, QtCore, uic

filepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-1])
basepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-2])
sys.path.append(basepath)
from lib import debug, utilsTray


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


type_dir = os.path.join(basepath,"type")
debug.info(type_dir)
options_ui_file = os.path.join(basepath,"lib-ui","selectionBox.ui")
scroll_ui_file  = os.path.join(basepath,"lib-ui","scrollWidget.ui")
textBox_ui_file = os.path.join(basepath,"lib-ui","textBox.ui")

config_file = os.path.join(homeconfig,"tray-server.ini")
app_lock_file = os.path.join(tempfile.gettempdir(),"tray-server-{0}.lock".format(os.environ['USER']))
debug.info(app_lock_file)
app_icon = os.path.join(basepath,"lib-ui","paf.png")
pidgin_notity_icon = os.path.join(basepath,"lib-ui","pidgin.png")
config_parser = ConfigParser.ConfigParser()
options_dict = {}

rbhus_notify_ids = {}

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
    options_dict['per-app-framework'] = options_ui.checkBox_paf_enable.checkState()
    options_dict['notify-app-changes'] = options_ui.checkBox_paf_notify.checkState()
    options_dict['pidgin-notify'] = options_ui.checkBox_pidgin.checkState()
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


class pidginNotify(QtCore.QObject):
  msg_received = QtCore.pyqtSignal(object)
  not_connected = QtCore.pyqtSignal()
  connected = QtCore.pyqtSignal()
  listening = QtCore.pyqtSignal()

  def __init__(self):
    super(pidginNotify, self).__init__()
    self.dbus_loop = None
    self.bus = None
    self.purple = None
    self.isAlive = False

  def start(self):
    self.dbus_loop = dbus.mainloop.pyqt5.DBusQtMainLoop(set_as_default=True)
    self.bus = dbus.SessionBus(mainloop=self.dbus_loop)
    self.connectToPidgin()

  def startListening(self):
    self.purple.connect_to_signal("ReceivedImMsg", self.receive_msg)
    self.purple.connect_to_signal("SendingImMsg", self.receive_msg)
    debug.info("started listening")
    self.listening.emit()

  def connectToPidgin(self):
    try:
      self.purple = self.bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")

      debug.info("connected to pidgin")
      self.connected.emit()
    except:
      self.not_connected.emit()
      debug.error(sys.exc_info())

  def isConnected(self):
    if(self.purple):
      try:
        self.bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
        if(self.isAlive == False):
          self.not_connected.emit()
          debug.info("re-connected")
        debug.info("connected")
        self.isAlive = True
      except:
        self.isAlive = False
        debug.error("re-disconnected")

  def receive_msg(self, *args):
    self.msg_received.emit(args)


class rbhusNotify(QtCore.QThread):
  notify = QtCore.pyqtSignal(object)

  def __init__(self):
    super(rbhusNotify, self).__init__()

  def run(self):
    while(True):
      getNotifications = utilsTray.getNotifications()
      if(getNotifications):
        self.notify.emit(getNotifications)
      time.sleep(2)


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
  pidginConnectTimer = QtCore.QTimer()
  pidginReConnectTimer = QtCore.QTimer()
  pidgin = pidginNotify()

  changePoll = appChangedPoll()
  changePoll.start()

  rbhusNotifies = rbhusNotify()
  rbhusNotifies.start()
  options_ui = uic.loadUi(options_ui_file)
  scroll_ui = uic.loadUi(scroll_ui_file)
  scroll_ui.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
  scroll_ui.setWindowTitle("rbhus-notifications")
  scroll_ui.pushButton_ok.clicked.connect(lambda a, s = scroll_ui: hide_scroll_ui(s,a))
  update_config(options_ui)
  options_ui.pushButton_ok.clicked.connect(lambda a, s = options_ui: hide_options_ui(s,a))
  options_ui.checkBox_paf_enable.clicked.connect(lambda a, s = options_ui: write_config(s))
  options_ui.checkBox_paf_notify.clicked.connect(lambda a, s=options_ui: write_config(s))
  options_ui.checkBox_pidgin.clicked.connect(lambda a, s=options_ui: write_config(s))
  trayIcon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(app_icon), app)
  trayIcon.activated.connect(lambda action, tray=trayIcon,ui=options_ui: action_triggered(action,tray,ui))
  menu = QtWidgets.QMenu()
  exitAction = menu.addAction("Exit")
  scrollMenuAction = menu.addAction("rbhus-notifications")
  trayIcon.setContextMenu(menu)
  exitAction.triggered.connect(quit)
  scrollMenuAction.triggered.connect(lambda s ,scroll_ui=scroll_ui:show_rbhus_notify(scroll_ui))
  trayIcon.setToolTip("tray-server")
  trayIcon.show()
  changePoll.app_changed.connect(lambda s, tray=trayIcon : run_per_app(tray, s))
  rbhusNotifies.notify.connect(lambda s, scroll_ui=scroll_ui: rbhus_notify(scroll_ui, s))

  pidginConnectTimer.timeout.connect(pidgin.connectToPidgin)
  pidgin.connected.connect(pidgin.startListening)
  pidgin.msg_received.connect(lambda s, tray=trayIcon: notity_pidgin_received_msg(tray,s))
  pidgin.not_connected.connect(lambda timeout=2000: pidginConnectTimer.start(timeout))
  pidgin.listening.connect(pidginConnectTimer.stop)
  pidgin.start()
  pidginReConnectTimer.timeout.connect(pidgin.isConnected)
  pidginReConnectTimer.start(2000)

  app_lock(trayIcon)
  run_once()
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
      debug.info(p.cmdline()[1])
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

def hide_scroll_ui(scroll_ui,arg):
  scroll_ui.hide()



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
    args[-1].setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
    args[-1].show()
    args[-1].setWindowTitle("tray-server")
    args[-1].move(QtGui.QCursor.pos() - QtCore.QPoint(0,args[-1].height()))
    update_config(args[-1])
    args[-1].raise_()



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
    tray.showMessage(args[0][1].split("@")[0],args[0][2],msecs=10000*10000,icon=QtWidgets.QSystemTrayIcon.Information)

def rbhus_notify(scroll_ui,*args):
  oldno = len(rbhus_notify_ids.keys())
  for x in args[0]:
    if(not rbhus_notify_ids.has_key(x['id'])):

      msg_box = uic.loadUi(textBox_ui_file)
      msg_box.setParent(scroll_ui)
      msg_box.groupBox.setTitle(x['title'])
      msg_box.msgBox.setText(x['msg'])
      msg_box.pushButton_open.clicked.connect(lambda s,id=x['id'],type_script=x['type_script'],type_script_args=x['type_script_args']: rbhus_notify_open_types(id,type_script,type_script_args))
      msg_box.pushButton_done.clicked.connect(lambda s,id=x['id']: rbhus_notify_done(id))
      scroll_ui.verticalLayout_2.addWidget(msg_box)
      rbhus_notify_ids[x['id']] = msg_box
      debug.info(x)
  newno = len(rbhus_notify_ids.keys())
  if(oldno != newno):
    show_rbhus_notify(scroll_ui)


def rbhus_notify_open_types(id,type_script,type_script_args):
  type_script_exe = os.path.join(type_dir,type_script)
  type_script_exe_with_args = type_script_exe +" "+ type_script_args
  p = subprocess.Popen(type_script_exe_with_args,shell=True,stderr=subprocess.PIPE, stdout=subprocess.PIPE)
  out = p.communicate()[0]
  if(p.returncode != 0):
    debug.error(out)
  else:
    debug.info(out)


def rbhus_notify_done(id):
  debug.info(id)
  rbhus_notify_ids[id].deleteLater()
  utilsTray.seeNotification(id)
  del(rbhus_notify_ids[id])


def show_rbhus_notify(scroll_ui):
  scroll_ui.show()
  screenGeometry = QtWidgets.QApplication.desktop().availableGeometry()
  screenGeo = screenGeometry.bottomRight()
  msgGeo =scroll_ui.frameGeometry()
  msgGeo.moveBottomRight(screenGeo)
  scroll_ui.move(msgGeo.topLeft())
  scroll_ui.raise_()



def clearLayout(layout):
  while layout.count() > 0:
    item = layout.takeAt(0)
    if not item:
      continue
    w = item.widget()
    if w:
      w.deleteLater()

if __name__ == '__main__':
  main()
