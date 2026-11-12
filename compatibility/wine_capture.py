"""PIL screenshots for AALC using the host's Limbus-only XComposite bridge."""
import io
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image


def crop_client(image, client_rect, window_rect):
    left, top, right, bottom = client_rect
    size = (right - left, bottom - top)
    if image.size == size:
        return image
    wl, wt, wr, wb = window_rect
    if image.size != (wr - wl, wb - wt):
        raise RuntimeError(f'Game screenshot geometry changed: {image.size}, client {size}')
    return image.crop((left - wl, top - wt, right - wl, bottom - wt))


def send_template_toast(title='AALC', msg='', *args, **kwargs):
    """Use the Linux notification service for upstream's translated toast text."""
    from module.logger import log
    try:
        info = json.loads(Path(__file__).with_name('bridge.json').read_text())
        parsed = urllib.parse.urlsplit(info['url'])
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path != '/frame.png':
            raise RuntimeError('Invalid local notification bridge URL')
        body = msg if isinstance(msg, str) else '\n'.join(str(line) for line in msg)
        request = urllib.request.Request(
            urllib.parse.urlunsplit(parsed._replace(path='/notify')),
            data=json.dumps({'title': title, 'body': body}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}, method='POST')
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(request, timeout=7) as response:
            if response.status != 204:
                raise RuntimeError('Desktop notification was not accepted')
        log.debug('Linux 桌面通知发送成功')
        return True
    except Exception as e:
        log.warning(f'Linux 桌面通知发送失败: {e}')
        return False


def capture(gray=True, state_path=None):
    """Return a fresh client-area image, or raise if the bridge/window is unavailable.

    The caller restores minimized game windows using AALC's existing Handle API.
    ``state_path`` defaults to bridge.json beside this module.
    """
    state_path = Path(state_path) if state_path else Path(__file__).with_name('bridge.json')
    info = json.loads(state_path.read_text())
    parsed = urllib.parse.urlsplit(info['url'])
    if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or parsed.path != '/frame.png':
        raise RuntimeError('Invalid local screenshot bridge URL')
    # Desktop/system proxy variables must never redirect this local connection.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(info['url'], timeout=5) as response:
            data = response.read()
    except urllib.error.HTTPError as e:
        try:
            message = json.loads(e.read())['error']
        except (ValueError, KeyError):
            message = f'Screenshot bridge returned HTTP {e.code}'
        raise RuntimeError(message) from e
    with Image.open(io.BytesIO(data)) as image:
        image.load()
        from module.game_and_screen import screen
        image = crop_client(image, screen.handle.rect(True), screen.handle.rect(False))
        return image.convert('L' if gray else 'RGB')
