import requests
import json
import types
import pprint
import logging

class SeaMicroAPIError(Exception):
	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

LOGGER = logging.getLogger('SeaMicroAPI')


class SeaMicroAPI:
	RESPONSE_CODES = {
		200: 'OK',
		202: 'Accepted',
		304: 'Not Modified',
		400: 'Bad Request',
		401: 'Unauthorized',
		403: 'Forbidden',
		404: 'Not Found',
		500: 'Internal Server Error',
		501: 'Internal Server Error (not implemented)'
	}

	def __init__(self, hostname='seamicro', use_ssl=True, verify_ssl=True, api_version='v0.9'):
		self.hostname = hostname
		self.protocol = "http"
		self.api_version = api_version
		self.verify_ssl = verify_ssl
		self.token = ""
		if use_ssl:
			self.protocol = "https"

		self.base_uri = "%s://%s/%s" % (self.protocol, self.hostname, self.api_version)

	# the v0.9 resources, except for techsupport, do not accept key/value pairs, 
	# so we'll create these silly parameter strings ourselves.
	def assemble_url_stupidly(self, location, params={ }):
		param_string = "&".join(filter(None, params.values()))
		uri = "%s?%s" % (location, param_string)
		url = "/".join([ self.base_uri, uri ])

		return url

	def decode_response(self, response):
		"""
		Handle the response object, and raise exceptions if errors are found.
		"""
		url = response.url
		if response.status_code not in (200, 202, 304):
			http_status_code = response.status_code
			raise SeaMicroAPIError('Got HTTP response code %d - %s for %s' % (http_status_code, self.RESPONSE_CODES.get(http_status_code, 'Unknown!'), url))

		json_data = response.json
		json_rpc_code = int(json_data['error']['code'])
		if json_rpc_code not in (200, 202, 304):
			raise SeaMicroAPIError('Got JSON RPC error code %d: %s for %s' % (json_rpc_code, self.RESPONSE_CODES.get(json_rpc_code, 'Unknown!'), url))
		return json_data

	def send_request_sensibly(self, location, params):
		params.update({ 'token': self.token })
		url = "/".join([ self.base_uri, location ])
		r = requests.get(url, verify=self.verify_ssl, params=params)
		return self.decode_response(r)

	def send_request(self, location, params):
		params.update({ 'token': self.token })
		url = self.assemble_url_stupidly(location, params)
		LOGGER.info('URL: %s' % url)

		r = requests.get(url, verify=self.verify_ssl)
		return self.decode_response(r)

	def login(self, username=None, password=None):
		self.username = username
		location = "login"
		decoded_json_response = self.send_request(location, params={ 'username': username, 'password': password })
		self.token = decoded_json_response['result']

	def logout(self):
		location = "logout"
		decoded_json_response = self.send_request(location, params={ })

	def cards(self):
		location = "cards"
		decoded_json_response = self.send_request(location, params={ })

		pprint.pprint(decoded_json_response)

	def cards_all(self):
		location = "cards/all"
		decoded_json_response = self.send_request(location, params={ })

		pprint.pprint(decoded_json_response)

	def logs(self):
		location = "system/logs"
		decoded_json_response = self.send_request(location, params={ })
		return decoded_json_response['result']

	# this is the only command that actually works in a reasonable way,
	# so we'll walk around the above hoops and just send the request.
	def tech_support(self):
		location = "system/techsupport"
		# Okay, this is brain damaged, but let me explain.
		# the parameter is required for the scope, but isn't accepted for the authentication
		# token. So since we are just using the values in the params dict for now, we just
		# make the value itself a key=value 
		params = { 'scope': 'scope=brief' }

		decoded_json_response = self.send_request(location, params=params)
		return decoded_json_response['result']


def main():
	sm = SeaMicroAPI(hostname="192.168.142.10", use_ssl=True, verify_ssl=False)
	sm.login(username='admin', password='seamicro')
	sm.cards()
	sm.cards_all()
	print sm.logs()
	print sm.tech_support()
	sm.logout()

if __name__ == '__main__':
	main()