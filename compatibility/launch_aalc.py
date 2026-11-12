#!/usr/bin/python3
"""Launch AALC beside Limbus in the existing Steam/Proton container."""
import configparser
import fcntl
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time

COMPAT = Path(__file__).resolve().parent
ROOT = COMPAT.parent


def game_pid():
    result = subprocess.run(['pgrep', '-x', 'LimbusCompany.e'], capture_output=True, text=True)
    return next(iter(result.stdout.splitlines()), None)


def show_existing():
    with socket.create_connection(('127.0.0.1', 62333), timeout=2) as connection:
        # Upstream's empty command arguments only restore its main window.
        connection.sendall(b'|')


def main():
    lock = (COMPAT / 'launcher.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        show_existing()
        return

    logs = ROOT / 'logs'
    logs.mkdir(exist_ok=True)
    log_path = logs / 'linux-launcher.log'
    with log_path.open('a', buffering=1) as log:
        print('\nLaunch', time.strftime('%Y-%m-%d %H:%M:%S'), file=log)
        pid = game_pid()
        if pid is None:
            subprocess.Popen(['flatpak', 'run', 'com.valvesoftware.Steam', '-applaunch', '1973530'],
                             stdout=log, stderr=log)
            deadline = time.monotonic() + 90
            while pid is None and time.monotonic() < deadline:
                time.sleep(1)
                pid = game_pid()
        if pid is None:
            raise RuntimeError('Steam did not start Limbus Company; start the game and retry.')

        env = dict(v.split('=', 1) for v in Path(f'/proc/{pid}/environ').read_text().split('\0') if '=' in v)
        info = configparser.ConfigParser(strict=False)
        info.read(f'/proc/{pid}/root/.flatpak-info')
        instance = info['Instance']['instance-id']
        tool = Path(env['STEAM_COMPAT_TOOL_PATHS'].split(':')[0])
        wine = tool / 'files/bin/wine'
        if not wine.is_file():
            raise RuntimeError(f'Cannot find the running game Proton loader: {wine}')

        state = COMPAT / 'bridge.json'
        state.unlink(missing_ok=True)
        bridge = subprocess.Popen(['/usr/bin/python3', str(COMPAT / 'capture_bridge.py'),
                                   '--state', str(state)], stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 5
            while not state.exists() and time.monotonic() < deadline:
                if bridge.poll() is not None:
                    raise RuntimeError('The game screenshot bridge failed to start.')
                time.sleep(.05)
            if not state.exists():
                raise RuntimeError('The game screenshot bridge startup timed out.')

            keys = ['VK_DRIVER_FILES', 'VK_ICD_FILENAMES', 'VK_LAYER_PATH',
                    'VK_IMPLICIT_LAYER_PATH', 'WINENTSYNC', 'NVIDIA_WINE_DLL_DIR',
                    '__GLVND_DISALLOW_PATCHING', 'WINEPREFIX', 'WINEESYNC', 'WINEFSYNC',
                    'WINEDLLPATH', 'WINEDLLOVERRIDES', 'LD_LIBRARY_PATH', 'DISPLAY',
                    'XAUTHORITY', 'XDG_RUNTIME_DIR', 'WAYLAND_DISPLAY']
            marker = COMPAT / 'session-started'
            marker.unlink(missing_ok=True)
            command = ['flatpak', 'enter', instance, '/usr/bin/env']
            command += [key + '=' + env[key] for key in keys if key in env]
            command += ['WINEDEBUG=-all', '/bin/sh', '-c', 'cd "$1" && shift && exec "$@"',
                        'sh', str(ROOT), str(wine), str(ROOT / 'diagnostics/python/python.exe'),
                        str(COMPAT / 'compat_bootstrap.py'), *sys.argv[1:]]
            result = subprocess.run(command, stdout=log, stderr=log)
            if result.returncode or not marker.exists():
                raise RuntimeError('AALC did not complete startup; see logs/linux-launcher.log.')
        finally:
            bridge.terminate()
            try:
                bridge.wait(timeout=3)
            except subprocess.TimeoutExpired:
                bridge.kill()
                bridge.wait()
            state.unlink(missing_ok=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        text = f'AALC 启动失败：{error}\n日志：{ROOT / "logs/linux-launcher.log"}'
        print(text, file=sys.stderr)
        if shutil.which('kdialog'):
            subprocess.run(['kdialog', '--error', text])
        raise SystemExit(1)
