#!/usr/bin/env bash
cat /etc/autofs/auto.home | grep -i stor3: | gawk '{print "rsync -av /etc/xdg/autostart/tray-server.py.desktop /home/"$1"/.config/autostart/ ; chown "$1":artist /home/"$1"/.config/autostart -Rv"}' | sh -v
