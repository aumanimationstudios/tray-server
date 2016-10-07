#!/usr/bin/env python2
#-*- coding: utf-8 -*-
__author__ = "Shrinidhi Rao"
__license__ = "GPL"
__email__ = "shrinidhi666@gmail.com"

import MySQLdb
import MySQLdb.cursors
import time
import sys
import socket
import os
import tempfile
import debug

os.environ["QT_GRAPHICSSYSTEM"] = "native"

hostname = socket.gethostname()
tempDir = tempfile.gettempdir()

dbHostname = "blues2"
dbPort = "3306"
dbDatabase = "trayServer"

try:
  dbHostname = os.environ['trayServer_dbHostname']
except:
  pass
try:
  dbPort = os.environ['trayServer_dbPort']
except:
  pass
try:
  dbDatabase = os.environ['trayServer_dbDatabase']
except:
  pass

if (sys.platform.find("win") >= 0):
  username = os.environ['USERNAME']
if (sys.platform.find("linux") >= 0):
  username = os.environ['USER']


class dbTray:
  """database querying class for tray-server"""

  def __init__(self):
    self.__conn = self._connRbhus()

  def __del__(self):
    try:
      self.__conn.close()
    except:
      debug.error(str(sys.exc_info()))
    # debug.debug("Db connection closed" + "\n")

  def _connDb(self, hostname, port, dbname):
    try:
      conn = MySQLdb.connect(host=hostname, port=port, db=dbname)
      conn.autocommit(1)
    except:
      raise
    return (conn)

  def _connRbhus(self):
    while (1):
      try:
        con = self._connDb(hostname=dbHostname, port=int(dbPort), dbname=dbDatabase)
        # debug.debug("Db connected")
        return (con)
      except:
        debug.error("Db not connected : " + str(sys.exc_info()))
      time.sleep(1)

  def execute(self, query, dictionary=False):
    while (1):
      try:
        if (dictionary):
          cur = self.__conn.cursor(MySQLdb.cursors.DictCursor)
        else:
          cur = self.__conn.cursor()
        cur.execute(query)
        # debug.debug(query)
        if (dictionary):
          try:
            rows = cur.fetchall()
          except:
            debug.error("fetching failed : " + str(sys.exc_info()))

          cur.close()
          if (rows):
            return (rows)
          else:
            return (0)
        else:
          cur.close()
          return (1)
      except:
        debug.error("Failed query : " + str(query) + " : " + str(sys.exc_info()))
        if (str(sys.exc_info()).find("OperationalError") >= 0):
          time.sleep(1)
          try:
            cur.close()
          except:
            pass
          try:
            self._conn.close()
          except:
            pass
          self.__conn = self._connRbhus()
          continue
        else:
          try:
            cur.close()
          except:
            pass
          raise