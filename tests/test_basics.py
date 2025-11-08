import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from portfolio.app import create_app

class BasicsTestCase(unittest.TestCase):
    def setUp(self):
        os.environ['SECRET_KEY'] = 'test-secret-key'
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        self.app_context.pop()

    def test_app_exists(self):
        self.assertIsNotNone(self.app)

    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)