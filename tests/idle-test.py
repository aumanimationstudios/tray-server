from Xlib import display
import time

root_x = None
root_y = None
idleTime = 0
idleTime_startCounter = 0

while(True):


  data = display.Display().screen().root.query_pointer()._data
  if((root_x != data['root_x']) or (root_y != data['root_y'])):
    root_x = data['root_x']
    root_y = data['root_y']
    if(idleTime_startCounter != 0):
      idleTime_startCounter = 0
  else:
    if(idleTime_startCounter == 0):
      idleTime_startCounter = time.time()
    else:
      if((time.time() - idleTime_startCounter) >= 10):
        print("idleing more than 10 sec")

  time.sleep(1)
