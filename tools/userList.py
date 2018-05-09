#!/usr/bin/env python2
#-*- coding: utf-8 -*-
__author__ = "Shrinidhi Rao"
__license__ = "GPL"
__email__ = "shrinidhi666@gmail.com"

import sys
import os
import argparse
from PyQt5 import QtWidgets, QtGui, QtCore, uic


filepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-1])
basepath = os.sep.join(os.path.abspath(__file__).split(os.sep)[0:-2])
sys.path.append(basepath)
import lib.debug
import lib.utilsTray



tableList_ui = os.path.join(basepath,"lib-ui","tableList.ui")
icon = os.path.join(basepath,"lib-ui","paf.png")
lib.debug.debug(tableList_ui)


parser = argparse.ArgumentParser()
parser.add_argument("--ui",dest="ui",action="store_true",help="show using the qt ui")
args = parser.parse_args()


users = lib.utilsTray.getUsers()

if(users):
  for x in users:
    print(str(x['host']).ljust(20,"-") + " : " + x['user'])

  if(args.ui):
    app = QtWidgets.QApplication(sys.argv)
    ui = uic.loadUi(tableList_ui)
    icon_ui = QtGui.QIcon(icon)
    ui.setWindowIcon(icon_ui)
    ui.setWindowTitle("users list")
    ui.tableWidget.setRowCount(len(users))
    ui.tableWidget.setColumnCount(2)
    rowCount = 0
    for x in users:
      ui.tableWidget.setItem(rowCount,0,QtWidgets.QTableWidgetItem(x['user']))
      ui.tableWidget.setItem(rowCount,1, QtWidgets.QTableWidgetItem(x['host']))
      rowCount += 1
    ui.show()
    sys.exit(app.exec_())




