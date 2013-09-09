CaptainSoul
=====

Netsoul client with python2.7, twisted, pygtk and pynotify

for instal and upgrade you could use pip:
```sh
sudo pip install --upgrade CatpainSoul
```

if you don't have notification install pynotify

and install a notification daemon like xfce4-notifyd

works directly on the dump

for archlinux do:
```sh
pacman -Sy twisted pygtk python2-notify
```

for the dump you can launch boot.sh in the xinitrc like that
```sh
xterm -e ./boot.sh
```

it will ask you for your sudo password in order to kill dump's netsoul and start cptsoul

For Windows:

- Install Python 2.7 (http://www.python.org/download/releases/2.7/)
- Install twisted (http://twistedmatrix.com/trac/wiki/Downloads) with zope.interface (https://pypi.python.org/pypi/zope.interface#download)
- Install pygtk all in one installer (http://www.pygtk.org/downloads.html)
- Rename cptsoul to cptsoul.pyw
- Run cptsoul.pyw

Features:

- Always actif log
- Contact list
- Chat
- Notification
- File transfer

To do:

- Blacklist
- Tab/Window chat
