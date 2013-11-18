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
    # so the below function builds them manually
    def assemble_url_legacy(self, location, params={ }):
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
        
        json_data = json.loads(response.text)

        if not json_data:
            raise SeaMicroAPIError('No JSON Data Found from %s: just got %s' % (url, response.text))
        json_rpc_code = int(json_data['error']['code'])
        if json_rpc_code not in (200, 202, 304):
                raise SeaMicroAPIError('Got JSON RPC error code %d: %s for %s' % (json_rpc_code, self.RESPONSE_CODES.get(json_rpc_code, 'Unknown!'), url))
        return json_data

    def send_get(self, location, params):
        params.update({ 'token': self.token })
        url = "/".join([ self.base_uri, location ])
        r = requests.get(url, verify=self.verify_ssl, params=params)
        return self.decode_response(r)

    def send_get_legacy(self, location, params):
        params.update({ 'token': self.token })
        url = self.assemble_url_legacy(location, params)
        LOGGER.info('URL: %s' % url)

        r = requests.get(url, verify=self.verify_ssl)
        return self.decode_response(r)
    
    def send_put_legacy(self, location, params):
        #removed the line below since the only current PUT command
        #serverPowerByName adds the token info manually because
        #the arguments are order-dependant
        #params.update({ 'token': self.token })
        
        url = self.assemble_url_legacy(location, params)
        LOGGER.info('URL: %s' % url)
        headers = {'content-type': 'text/json'}

        r = requests.put(url, headers=headers, verify=self.verify_ssl)
        return self.decode_response(r)

    def login(self, username=None, password=None):
        self.username = username
        location = "login"
        decoded_json_response = self.send_get_legacy(location, params={ 'username': username, 'password': password })
        self.token = decoded_json_response['result']

    def logout(self):
        location = "logout"
        decoded_json_response = self.send_get_legacy(location, params={ })

    def cards(self):
        location = "cards"
        decoded_json_response = self.send_get_legacy(location, params={ })

        return decoded_json_response['result']

    def cards_all(self):
        location = "cards/all"
        decoded_json_response = self.send_get_legacy(location, params={ })

        return decoded_json_response['result']
        
    def servers(self):
        location = "servers"
        decoded_json_response = self.send_get_legacy(location, params={ })

        return decoded_json_response['result']

    def servers_all(self):
        location = "servers/all"
        decoded_json_response = self.send_get_legacy(location, params={ })

        return decoded_json_response['result']

    # below grabs detailed server info based on server's name, e.g. "17/0"
    def serverByName(self, serverName):
        serverIndex = self.indexForServer(serverName)    
        location = "servers/%s" % (serverIndex)

        return self.send_get_legacy(location, params={ })['result']
    
    # below issues power on/off/reset command
    # newStatus must be ['Power-On', 'Power-Off', 'Reset']
    # doPxe boolean to accompany Power-On & Reset
    # force boolean to accompany Power-Off
    # arguments are order-dependant at the system,
    # so we're manually creating post string here
    def serverPowerByName(self, serverName, newStatus, doPxe=False, force=False):
        serverIndex = self.indexForServer(serverName)
        location = "servers/%s" % (serverIndex)
        
        params = {}
        if newStatus in ['Power-On', 'Reset']:
            if doPxe:
                params['params'] = "action=%s&using-pxe=true&%s" % (newStatus,self.token)
            else:
                params['params'] = "action=%s&using-pxe=false&%s" % (newStatus,self.token)
        elif newStatus == 'Power-Off':
            if force:
                params['params'] = "action=%s&force=true&%s" % (newStatus,self.token)
            else:
                params['params'] = "action=%s&force=false&%s" % (newStatus,self.token)
        else:
            return False
        
        self.send_put_legacy(location, params=params)['result']
        return True
    
    # because API v0.9 uses arbitrary indexing, this function converts a server id
    # to an index that can be used for detailed outputs & commands
    def indexForServer(self, serverName):
        location = "servers"
        serverDict = self.send_get_legacy(location, params={ })['result']['serverId']
        
        for serverIndex, serverId in serverDict.items():
            if serverId == serverName:
                return serverIndex
        
        return False
    
    def logs(self):
        location = "system/logs"
        decoded_json_response = self.send_get_legacy(location, params={ })
        return decoded_json_response['result']

    # this is the only command that takes a key-value pair,
    # so we'll use the proper send_get method
    def tech_support(self):
        location = "system/techsupport"
        params = { 'scope': 'scope=brief' }

        decoded_json_response = self.send_get(location, params=params)
        return decoded_json_response['result']

# Example of usage
def main():
    sm = SeaMicroAPI(hostname="10.216.142.87", use_ssl=False, verify_ssl=False)
    sm.login(username='admin', password='seamicro')
    
    #pprint.pprint(sm.servers_all())
    #pprint.pprint(sm.logs())
    #pprint.pprint(sm.serverByName("60/0"))
    #pprint.pprint(sm.serverPowerByName("60/0",newStatus="Power-On", doPxe=True))
    #pprint.pprint(sm.serverPowerByName("60/0",newStatus="Reset", doPxe=False))
    #pprint.pprint(sm.serverPowerByName("60/0",newStatus="Power-Off", force=True))


    sm.logout()

if __name__ == '__main__':
        main()

