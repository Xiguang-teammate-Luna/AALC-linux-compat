"""Reuse the official frozen dependencies with scoped Wine compatibility fixes."""
import os
import sys
import marshal
import types
from pathlib import Path

root = Path(__file__).resolve().parent.parent
internal = root / '_internal'
compat = root / 'compatibility'
os.chdir(root)
os.environ['QT_QPA_PLATFORMTHEME'] = 'windows'
sys._MEIPASS = str(internal)
sys._pyinstaller_pyz = str(compat / 'PYZ.pyz')
sys.frozen = True
sys.executable = str(root / 'AALC.exe')
stdlib = [p for p in sys.path if str(root / 'diagnostics' / 'python').lower() in p.lower()]
sys.path[:] = [str(internal / 'base_library.zip'), str(internal), str(compat)] + stdlib

for name in ('pyimod01_archive', 'pyimod02_importers', 'pyimod03_ctypes', 'pyimod04_pywin32'):
    m = types.ModuleType(name)
    m.__file__ = str(compat / (name + '.bin'))
    sys.modules[name] = m
    exec(marshal.loads((compat / (name + '.bin')).read_bytes()), m.__dict__)
    if name != 'pyimod01_archive':
        m.install()

for name in ('pyi_rth_inspect', 'pyi_rth_pyside6', 'pyi_rth_pkgutil',
             'pyi_rth_multiprocessing', 'pyi_rth_setuptools',
             'pyi_rth_pywintypes', 'pyi_rth_pythoncom'):
    exec(marshal.loads((compat / (name + '.bin')).read_bytes()), {'__name__': name})

# Reuse the upstream workflow, input adapters, settings and GUI, with scoped
# platform adapters for screenshots, desktop notifications and the weekly tab.
from module.automation.screenshot import ScreenShot
from wine_capture import capture, send_template_toast
from app import windows_toast
windows_toast._send_template_toast = send_template_toast
from module.game_and_screen import screen
from window_compat import install as install_window_compat
install_window_compat()
from time import sleep

def bridge_screenshot(gray=True):
    if screen.handle.isMinimized:
        screen.handle.restore()
        sleep(0.2)
    return capture(gray)

# Preserve the upstream high-level dispatcher, simulator branch and locking.
ScreenShot.background_screenshot = staticmethod(bridge_screenshot)
ScreenShot.take_screenshot_gdi = staticmethod(bridge_screenshot)
ScreenShot.take_screenshot_pyautogui = staticmethod(bridge_screenshot)
print('AALC compatibility: Windows theme + XComposite screenshot bridge', flush=True)
from module.config import cfg
# This compatibility layer is pinned to the shipped V1.6.1 module archive.
# Keep image-resource updates available; do not replace the executable under it.
cfg.set_value('check_update', False)
from reward_compat import install as install_reward_compat
install_reward_compat()
from shop_compat import install as install_shop_compat
install_shop_compat()

from app.my_app import MainWindow
original_init = MainWindow.__init__

def compatible_init(self, argv):
    original_init(self, argv)
    (compat / 'session-started').write_text(str(os.getpid()))
MainWindow.__init__ = compatible_init

namespace = {'__name__' : '__main__', '__file__': str(root / 'main.py'), '__package__': None}
sys.argv[0] = str(root / 'AALC.exe')
exec(marshal.loads((compat / 'main.bin').read_bytes()), namespace)
