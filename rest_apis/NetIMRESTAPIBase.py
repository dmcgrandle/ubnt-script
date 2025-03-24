#/**********************************/
#/*       Copyright (c) 2020       */
#/*   Riverbed Technology, Inc.    */
#/*      All Rights Reserved.      */
#/**********************************/

import json
import requests
from requests.auth import HTTPBasicAuth
import urllib3

class NetIMRESTAPIBase:
    def __init__ (self, server_address, protocol='https', port=8543, version='v1', username='admin', password='admin'):
        self.base_url = '%s://%s:%s' % (protocol, server_address, port)
        self.api_url = self.base_url + '/api/netim/' + version

        self.username = username
        self.password = password
        self.session = self.get_session (self.username, self.password)

    def get_session (self, username, password):
        session = requests.session()
        headers = {'Content-type': 'application/json'}

        # For basic authentication you should provide the log in information to the session
        session.auth = HTTPBasicAuth (username, password)
        session.headers.update (headers)
        urllib3.disable_warnings (urllib3.exceptions.InsecureRequestWarning)

        return session

    def get_json_from_resource (self, resource_url):
        json_dict = {}
        try:
            resp = self.session.get (resource_url, verify=False)
            # The response object is a conditional that evaluates to true for a successful response
            # but that includes codes in the 300 range. We shouldn't be getting redirected so
            # we're limiting the valid responses to the 200 range.
            if resp is not None:
                if resp.status_code >= 200 and resp.status_code < 300:
                    resp_text = resp.text
                    json_dict = json.loads(resp_text)
                else:
                    print (f"Unable to retrieve resource. Status code: {resp.status_code}")
            else:
                print (f"Unable to retrieve resource from URL: {resource_url}")
        except Exception as e:
            print (f"Exception getting data from: {resource_url}")
            print (e)
        return json_dict

    def post_data (self, resource_url, post_dict):
        post_json = json.dumps (post_dict)
        headers = {'content-type': 'application/json'}
        #response = requests.post(resource_url, data=post_json, auth=(self.username, self.password), headers=headers)
        response = self.session.post (resource_url, data=post_json, headers=headers, verify=False)
        print("Status code: ", response.status_code)
        if response.status_code == 200:
            return True
        else:
            print (response.text)
            return False
