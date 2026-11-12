"""Check preparation against a supplied official release without launching the game."""
import importlib.util
from pathlib import Path
import os
import shutil
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('prepare',REPO/'prepare.py')
prepare=importlib.util.module_from_spec(spec);spec.loader.exec_module(prepare)

@unittest.skipUnless(os.environ.get('AALC_TEST_RELEASE') and os.environ.get('AALC_TEST_PYTHON_ZIP'),
                     'Set AALC_TEST_RELEASE and AALC_TEST_PYTHON_ZIP to official local inputs')
class PrepareIntegration(unittest.TestCase):
    def test_prepare_and_reinstall_preserve_user_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'AALC'
            source=Path(os.environ['AALC_TEST_RELEASE'])
            (root/'assets/config').mkdir(parents=True)
            shutil.copy2(source/'AALC.exe',root/'AALC.exe')
            shutil.copy2(source/'assets/config/version.txt',root/'assets/config/version.txt')
            user=b'# private configuration\nteams: {}\n'
            weights=b'theme_pack_list: {}\n'
            (root/'config.yaml').write_bytes(user)
            (root/'theme_pack_list.yaml').write_bytes(weights)
            archive=Path(os.environ['AALC_TEST_PYTHON_ZIP'])
            first=prepare.prepare(root,archive)
            (root/'compatibility/local-marker').write_text('old adapter')
            second=prepare.prepare(root,archive)
            self.assertNotEqual(first,second)
            self.assertEqual((root/'config.yaml').read_bytes(),user)
            self.assertEqual((root/'theme_pack_list.yaml').read_bytes(),weights)
            self.assertEqual((second/'compatibility/local-marker').read_text(),'old adapter')
            self.assertEqual((root/'diagnostics/python/python313._pth').read_text(),
                             'python313.zip\n.\nimport site\n')
            self.assertTrue((root/'compatibility/PYZ.pyz').is_file())
            before=sorted(p.name for p in root.iterdir())
            (root/'assets/config/version.txt').write_text('V9.9.9')
            with self.assertRaises(ValueError):prepare.prepare(root,archive)
            self.assertEqual(before,sorted(p.name for p in root.iterdir()))
            self.assertEqual((root/'config.yaml').read_bytes(),user)

if __name__=='__main__':unittest.main()
