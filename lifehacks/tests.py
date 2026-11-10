import json
import os
import subprocess
import sys

from django.test import SimpleTestCase


class SettingsTests(SimpleTestCase):
    def load_settings(self, **variables):
        environment = {key: value for key, value in os.environ.items() if not key.startswith('DJANGO_')}
        environment.update(variables)
        return subprocess.run(
            [sys.executable, '-c',
             'import json; from lifehacks import settings as s; '
             'print(json.dumps([s.DEBUG, s.SESSION_COOKIE_SECURE, '
             's.CSRF_COOKIE_SECURE, s.SECURE_SSL_REDIRECT, s.ALLOWED_HOSTS]))'],
            env=environment, capture_output=True, text=True, check=False,
        )

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
