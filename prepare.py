#!/usr/bin/env python3
"""Install the compatibility layer beside an unpacked official AALC release."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import tempfile
import zipfile

SUPPORTED = 'V1.6.1'


def prepare(root, python_zip):
    from PyInstaller.archive.readers import CArchiveReader
    root = Path(root).expanduser().resolve()
    version = (root / 'assets/config/version.txt').read_text(encoding='utf-8').strip()
    if version != SUPPORTED:
        raise ValueError(f'Expected {SUPPORTED}, found {version}; do not use an unverified adapter')
    reader = CArchiveReader(str(root / 'AALC.exe'))
    names = ['PYZ.pyz', 'main', 'pyimod01_archive', 'pyimod02_importers',
             'pyimod03_ctypes', 'pyimod04_pywin32', 'pyi_rth_inspect',
             'pyi_rth_pyside6', 'pyi_rth_pkgutil', 'pyi_rth_multiprocessing',
             'pyi_rth_setuptools', 'pyi_rth_pywintypes', 'pyi_rth_pythoncom']
    missing = set(names) - reader.toc.keys()
    if missing:
        raise ValueError(f'Official executable startup members missing: {sorted(missing)}')
    with zipfile.ZipFile(python_zip) as archive:
        if not {'python.exe', 'python313.zip', 'python313.dll'} <= set(archive.namelist()):
            raise ValueError('Provide the official Windows x86-64 Python 3.13 embeddable ZIP')
        # Prepare completely before replacing an existing compatibility directory.
        with tempfile.TemporaryDirectory(prefix='aalc-prepare-') as temporary:
            staged = Path(temporary)
            compat = staged / 'compatibility'
            shutil.copytree(Path(__file__).resolve().parent / 'compatibility', compat,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for name in names:
                (compat / (name if name == 'PYZ.pyz' else name + '.bin')).write_bytes(reader.extract(name))
            runtime = staged / 'python'
            runtime.mkdir()
            # The official embeddable distribution contains only top-level files.
            for item in archive.infolist():
                if item.is_dir() or Path(item.filename).name != item.filename:
                    raise ValueError(f'Unexpected embedded Python archive member: {item.filename}')
                (runtime / item.filename).write_bytes(archive.read(item))
            (runtime / 'python313._pth').write_text('python313.zip\n.\nimport site\n')
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            backup = root / ('linux-compat-backup-' + stamp)
            # Only integration files and snapshots are written. AALC config is never rewritten here.
            backup.mkdir()
            for name in ['config.yaml', 'theme_pack_list.yaml']:
                if (root / name).exists():
                    shutil.copy2(root / name, backup / name)
            targets = [(compat, root / 'compatibility'), (runtime, root / 'diagnostics/python')]
            replaced = []
            try:
                for source, target in targets:
                    old = backup / target.name
                    if target.exists():
                        target.rename(old)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    replaced.append((target, old))
                    shutil.copytree(source, target)
            except Exception:
                for target, old in reversed(replaced):
                    if target.exists():
                        shutil.rmtree(target)
                    if old.exists():
                        old.rename(target)
                raise
    return backup


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--aalc-dir', required=True, type=Path)
    p.add_argument('--python-zip', required=True, type=Path)
    args = p.parse_args()
    backup = prepare(args.aalc_dir, args.python_zip)
    print(f'Prepared {SUPPORTED}. Integration backup: {backup}')
    print(f'Launch: /usr/bin/python3 "{args.aalc_dir / "compatibility/launch_aalc.py"}"')


if __name__ == '__main__':
    main()
