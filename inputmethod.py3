#!/usr/bin/python3

from os import environ, listdir
from os.path import isdir, isfile, join
from re import search
from typing import Optional

def input_method_exist(im):
  if not im:
    return False
  for path in ["/etc/X11/xim.d", "/usr/etc/X11/xim.d"]:
    if isfile(join(path, im)):
      return True
    elif im == "fcitx" and isfile(join(path, "fcitx5")):
      return True
  return False

def get_current_input_method() -> Optional[str]:
  pattern = r'^export\s+(INPUT_METHOD|XMODIFIERS)=("@im=)?([A-Za-z0-9]+)(")?$'
  pattern_sysconfig = '^INPUT_METHOD="([A-Za-z0-9]+)"$'
  input_method = ""

  # find input_method in $HOME/.xim or $HOME/.i18n
  home = environ.get("HOME")
  # the first user session started via systemd is always the display manager's greeter
  # whose $HOME is, eg: /var/lib/sddm
  if not home.startswith("/home"):
    return None

  for conf in [".xim", ".i18n", ".profile", ".login"]:
    conf = join(home, conf)
    if isfile(conf):
      file = open(conf, "r")

      for line in file:
        find = search(pattern, line)
        if find:
          input_method = find.group(3)
          break

      file.close()
      if input_method:
        break

  # use user-specified INPUT_METHOD
  if input_method_exist(input_method):
    if input_method == "fcitx5":
      input_method = "fcitx"
    return input_method.lower()

  # try to use INPUT_METHOD in /etc/sysconfig/language
  if isfile("/etc/sysconfig/language"):
    file = open("/etc/sysconfig/language", "r")
    for line in file:
      find = search(pattern_sysconfig, line)
      if find:
        input_method = find.group(1)
        break
    file.close()

  if input_method_exist(input_method):
    if input_method == "fcitx5":
      input_method = "fcitx"
    return input_method.lower()

  # use language default
  lang = environ.get("LC_CTYPE")

  if lang:
    if lang.startswith("zh_"):
      lang = lang[0:5]
    else:
      lang = lang[0:lang.find('_')]
  else:
    lang = "en"

  inputmethods = []
  for path in ["/etc/X11/xim.d", "/usr/etc/X11/xim.d"]:
    path = join(path, lang)
    if isdir(path):
      inputmethods = [f for f in listdir(path) if isfile(join(path, f))]
  if not inputmethods:
    # leave INPUT_METHOD unset
    return None

  i = 0
  j = 0
  for im in inputmethods:
    arr = im.split("-")
    if j == 0:
      i = int(arr[0])
      input_method = arr[1]
      j += 1
      continue
    if int(arr[0]) < i:
      i = int(arr[0])
      input_method = arr[1]
      j += 1
  if input_method:
    if input_method == "fcitx5":
      input_method = "fcitx"
    return input_method.lower()
  return None

def print_environment_variables(input_method: Optional[str]):
  if input_method is None:
    # Leave INPUT_METHOD unset
    pass
  else:
    if input_method == "ibus":
      # If application uses the legacy IBus GTK IM module, ibus-ui-gtk3 is
      # unstable under a Wayland session
      # Use Wayland native input method protocol for GTK and Qt applications
      pass
    else:
      print("GTK_IM_MODULE={}".format(input_method))
      print("QT_IM_MODULE={}".format(input_method))

    # Set XMODIFIERS for X11 applications
    print("XMODIFIERS=@im={}".format(input_method))
    print("INPUT_METHOD={}".format(input_method))

input_method = get_current_input_method()
print_environment_variables(input_method)
