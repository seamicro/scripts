import argparse
import unittest
from seamicro_api import SeaMicroAPI

class TestSeaMicroAPIAuthentication(unittest.TestCase):
	def setUp(self):
		self.api = SeaMicroAPI(hostname="192.168.142.10", use_ssl=True, verify_ssl=False)

	def test_login_logout(self):
		self.api.login(username='admin', password='seamicro')
		self.api.logout()

	def test_bad_login(self):
		self.api.login(username='admin', password='badpass')

if __name__ == '__main__':
	unittest.main()