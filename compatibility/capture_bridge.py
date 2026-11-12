"""Serve Limbus XComposite frames and AALC's local desktop notifications."""
import ctypes as C
import io
import json
import os
import signal
import subprocess
from html import escape
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from PIL import Image


class XImage(C.Structure):
    _fields_ = [(n, t) for n, t in [
        ('width', C.c_int), ('height', C.c_int), ('xoffset', C.c_int),
        ('format', C.c_int), ('data', C.c_void_p), ('byte_order', C.c_int),
        ('bitmap_unit', C.c_int), ('bitmap_bit_order', C.c_int),
        ('bitmap_pad', C.c_int), ('depth', C.c_int),
        ('bytes_per_line', C.c_int), ('bits_per_pixel', C.c_int),
    ]]


class XWindowAttributes(C.Structure):
    _fields_ = [
        ('x', C.c_int), ('y', C.c_int), ('width', C.c_int), ('height', C.c_int),
        ('border_width', C.c_int), ('depth', C.c_int), ('visual', C.c_void_p),
        ('root', C.c_ulong), ('class_', C.c_int), ('bit_gravity', C.c_int),
        ('win_gravity', C.c_int), ('backing_store', C.c_int),
        ('backing_planes', C.c_ulong), ('backing_pixel', C.c_ulong),
        ('save_under', C.c_int), ('colormap', C.c_ulong),
        ('map_installed', C.c_int), ('map_state', C.c_int),
        ('all_event_masks', C.c_long), ('your_event_mask', C.c_long),
        ('do_not_propagate_mask', C.c_long), ('override_redirect', C.c_int),
        ('screen', C.c_void_p),
    ]


class Capture:
    def __init__(self):
        self.x = C.CDLL('libX11.so.6')
        self.co = C.CDLL('libXcomposite.so.1')
        self.x.XOpenDisplay.restype = C.c_void_p
        self.d = self.x.XOpenDisplay(None)
        if not self.d:
            raise RuntimeError('Cannot connect to the desktop X server')
        self.x.XDefaultRootWindow.argtypes = [C.c_void_p]
        self.x.XDefaultRootWindow.restype = C.c_ulong
        self.root = self.x.XDefaultRootWindow(self.d)
        self.x.XQueryTree.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_ulong),
            C.POINTER(C.c_ulong), C.POINTER(C.POINTER(C.c_ulong)), C.POINTER(C.c_uint)]
        self.x.XFetchName.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(C.c_char_p)]
        self.x.XFree.argtypes = [C.c_void_p]
        self.x.XGetGeometry.argtypes = [C.c_void_p, C.c_ulong] + [C.c_void_p] * 7
        self.x.XGetWindowAttributes.argtypes = [C.c_void_p, C.c_ulong, C.POINTER(XWindowAttributes)]
        self.x.XCloseDisplay.argtypes = [C.c_void_p]
        self.co.XCompositeNameWindowPixmap.argtypes = [C.c_void_p, C.c_ulong]
        self.co.XCompositeNameWindowPixmap.restype = C.c_ulong
        self.x.XGetImage.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_int,
            C.c_uint, C.c_uint, C.c_ulong, C.c_int]
        self.x.XGetImage.restype = C.POINTER(XImage)
        self.x.XDestroyImage.argtypes = [C.POINTER(XImage)]
        self.x.XFreePixmap.argtypes = [C.c_void_p, C.c_ulong]
        self.x.XSync.argtypes = [C.c_void_p, C.c_int]
        self.errors = []
        self.error_cb = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_void_p)(self._error)
        self.x.XSetErrorHandler.argtypes = [C.c_void_p]
        self.x.XSetErrorHandler(self.error_cb)

    def close(self):
        if self.d:
            self.x.XCloseDisplay(self.d)
            self.d = None

    def _error(self, display, error):
        self.errors.append(True)
        return 0

    def window(self):
        root = C.c_ulong(); parent = C.c_ulong()
        children = C.POINTER(C.c_ulong)(); count = C.c_uint()
        self.x.XQueryTree(self.d, self.root, C.byref(root), C.byref(parent),
                          C.byref(children), C.byref(count))
        try:
            for i in range(count.value):
                name = C.c_char_p()
                self.x.XFetchName(self.d, children[i], C.byref(name))
                try:
                    if name.value == b'LimbusCompany':
                        return children[i]
                finally:
                    if name:
                        self.x.XFree(name)
        finally:
            if children:
                self.x.XFree(children)
        raise RuntimeError('LimbusCompany window is not running')

    def frame(self):
        self.errors.clear()
        w = self.window()
        attr = XWindowAttributes()
        if not self.x.XGetWindowAttributes(self.d, w, C.byref(attr)) or attr.map_state != 2:
            raise RuntimeError('Game window must be restored from minimization')
        root = C.c_ulong()
        vals = [C.c_int(), C.c_int()] + [C.c_uint() for _ in range(4)]
        self.x.XGetGeometry(self.d, w, C.byref(root), *[C.byref(v) for v in vals])
        self.x.XSync(self.d, 0)
        if self.errors:
            raise RuntimeError('Cannot read the game window geometry')
        width, height = vals[2].value, vals[3].value
        pix = self.co.XCompositeNameWindowPixmap(self.d, w)
        self.x.XSync(self.d, 0)
        if self.errors:
            raise RuntimeError('Game window must be restored from minimization')
        im = None
        try:
            im = self.x.XGetImage(self.d, pix, 0, 0, width, height, 0xffffffff, 2)
            self.x.XSync(self.d, 0)
            if not im or self.errors:
                raise RuntimeError('Cannot read the game backing pixmap')
            v = im.contents
            if v.bits_per_pixel != 32:
                raise RuntimeError(f'Unsupported X image depth: {v.bits_per_pixel}')
            raw = C.string_at(v.data, v.bytes_per_line * height)
            return Image.frombytes('RGB', (width, height), raw, 'raw', 'BGRX', v.bytes_per_line)
        finally:
            if im:
                self.x.XDestroyImage(im)
            self.x.XFreePixmap(self.d, pix)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--state', required=True)
    args = p.parse_args()
    capture = Capture()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != '/notify':
                self.send_error(404)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 8192:
                    raise ValueError('Invalid notification size')
                payload = json.loads(self.rfile.read(length))
                title, body = payload['title'], payload['body']
                if not isinstance(title, str) or not isinstance(body, str):
                    raise ValueError('Notification text must be strings')
                subprocess.run(['/usr/bin/notify-send', '--app-name=AALC', '--',
                                title[:256], escape(body[:4000])], check=True, timeout=5)
                self.send_response(204)
                self.end_headers()
            except Exception as e:
                self.send_error(503, str(e))

        def do_GET(self):
            if self.path != '/frame.png':
                self.send_error(404)
                return
            try:
                frame = capture.frame()
                output = io.BytesIO()
                frame.save(output, format='PNG', compress_level=1)
                data = output.getvalue()
                self.send_response(200)
                self.send_header('Content-Type', 'image/png')
                self.send_header('Content-Length', str(len(data)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                data = json.dumps({'error': str(e)}).encode('utf-8')
                self.send_response(503)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        def log_message(self, *args):
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    server.timeout = 0.5
    state = Path(args.state)
    temporary = state.with_suffix(state.suffix + '.tmp')
    temporary.write_text(json.dumps({'url': f'http://127.0.0.1:{server.server_port}/frame.png', 'pid': os.getpid()}))
    temporary.replace(state)
    print('Capture bridge ready', server.server_port, flush=True)
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while running:
            server.handle_request()
    finally:
        server.server_close()
        capture.close()
        state.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
