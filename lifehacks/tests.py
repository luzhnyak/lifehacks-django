import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


class SettingsTests(SimpleTestCase):
    def load_settings(self, env_file=None, **variables):
        environment = {
            key: value for key, value in os.environ.items()
            if not key.startswith('DJANGO_') and key != 'PYTHON_DOTENV_DISABLED'
        }
        environment.update(variables)
        with TemporaryDirectory() as directory:
            root = Path(directory)
            settings_file = root / 'lifehacks' / 'settings.py'
            settings_file.parent.mkdir()
            shutil.copyfile(Path(__file__).with_name('settings.py'), settings_file)
            if env_file is not None:
                (root / '.env').write_text(env_file, encoding='utf-8')
            return subprocess.run(
                [sys.executable, '-c',
                 'import json, runpy, sys; from types import SimpleNamespace; '
                 's = SimpleNamespace(**runpy.run_path(sys.argv[1])); '
                 'print(json.dumps([s.DEBUG, s.SESSION_COOKIE_SECURE, '
                 's.CSRF_COOKIE_SECURE, s.SECURE_SSL_REDIRECT, s.ALLOWED_HOSTS]))',
                 str(settings_file)],
                env=environment, capture_output=True, text=True, check=False,
            )

    def test_supervisor_start_reads_production_dotenv_without_shell_exports(self):
        result = self.load_settings(env_file=(
            "DJANGO_DEBUG=false\n"
            "DJANGO_SECRET_KEY='test-file-key'\n"
            "DJANGO_ALLOWED_HOSTS=example.com\n"
        ))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [False, True, True, True, ['example.com']])

    def test_process_environment_takes_priority_over_dotenv(self):
        result = self.load_settings(
            env_file="DJANGO_DEBUG=true\nDJANGO_ALLOWED_HOSTS=wrong.example\n",
            DJANGO_DEBUG='false', DJANGO_SECRET_KEY='test-process-key',
            DJANGO_ALLOWED_HOSTS='example.com',
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [False, True, True, True, ['example.com']])

    def test_production_refuses_to_start_without_secret(self):
        result = self.load_settings()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY', result.stderr)

    def test_production_refuses_to_start_without_hosts(self):
        result = self.load_settings(DJANGO_SECRET_KEY='test-only')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_ALLOWED_HOSTS', result.stderr)

    def test_production_enables_https_protection(self):
        result = self.load_settings(DJANGO_SECRET_KEY='test-only', DJANGO_ALLOWED_HOSTS=' example.com, www.example.com ')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [False, True, True, True, ['example.com', 'www.example.com']])

    def test_local_http_supports_session_and_csrf_cookies(self):
        result = self.load_settings(DJANGO_DEBUG='true')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [True, False, False, False, ['localhost', '127.0.0.1']])

    def test_invalid_boolean_is_rejected(self):
        result = self.load_settings(DJANGO_DEBUG='treu')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_DEBUG must be a boolean', result.stderr)
