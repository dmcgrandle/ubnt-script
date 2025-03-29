#/**********************************/
#/*       Copyright (c) 2025       */
#/*   Riverbed Technology, Inc.    */
#/*      All Rights Reserved.      */
#/**********************************/

from datetime import datetime
import json
#ßimport sys
import time
#import socket
#import subprocess
#import re
#import random
import requests
from requests.auth import HTTPBasicAuth
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from rest_apis.DevicesAPI import DevicesAPI
from rest_apis.MetricClassesAPI import MetricClassesAPI
from rest_apis.NetworkMetricImportAPI import NetworkMetricImportAPI, METRIC_DATA_TEMPLATE

# "Silently skip certificate verification warning"
urllib3.disable_warnings(InsecureRequestWarning)

##################### CONFIGURATION ##################
#sys.path.append('/home/netimadmin/Riverbed/TE/3.1.4/TestEngine/service/linux/bin')

# "Access to NetIM Server"
NetIMCoreServer = 'netim'
NetIMCoreServerPort = '8543'

# Unifi credentials
UBNT_CONTROLLER = '192.168.2.1'
UBNT_API_KEY = 'SqRAbyer53Wh0MtcOaJuVDTlEMqVsXpF'

# NetIM API credentials
User = 'admin'
Password = 'admin'

# Routers
Routers = ['n21-rtr.cyberdyne.corp', 'n31-rtr.cyberdyne.corp']

# Input UDM
InputMetricClassName = 'Route-Table'

# Output UDM
OutputMetricClassName = 'Route-Changes'

# Frequency to be aligned with polling frequency of the input UDM (above)
Interval = 300

##################### CONFIGURATION ##################



# Example API call:
# curl -k -X GET 'https://192.168.2.1/proxy/network/integration/v1/sites' \
#  -H 'X-API-KEY: YOUR_API_KEY' \
#  -H 'Accept: application/json'

class UBNTRESTAPIBase:
    def __init__ (self, server_address, protocol='https', port=443, version='v1', api_key='none', password='none'):
        self.base_url = '%s://%s:%s' % (protocol, server_address, port)
        self.api_url = self.base_url + '/proxy/network/integration/' + version

        self.api_key = api_key
        self.password = password
        self.session = self.get_session (self.api_key, self.password)

    def get_session (self, api_key, password):
        session = requests.session()
        headers = {'Accept': 'application/json'}

        # password can be anything, but need a valid API key created in the Unifi network console:
        # Settngs -> Control Plane -> Integrations -> Create API Key
        session.auth = HTTPBasicAuth (api_key, password)
        session.headers.update (headers)
        # urllib3.disable_warnings (urllib3.exceptions.InsecureRequestWarning)
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

class UBNTClassesAPI (UBNTRESTAPIBase):
    def __init__ (self, server_address, protocol='https', port=8543, version='v1', api_key='admin', password='admin'):
        UBNTRESTAPIBase.__init__ (self, server_address, protocol, port, version, api_key, password)
        # /metric-classes - ??
        self.resource_url = self.api_url + '/sites'

    def get_all_metric_classes (self):
        'Get all metric classes'
        metric_classes_json = self.get_json_from_resource (self.resource_url)
        return metric_classes_json

    def get_metric_class_by_name (self, name):
        'Get metric class by its name'
        # Get all devices
        metric_classes_json = self.get_all_metric_classes ()

        metric_class_json = None
        for metric_class in metric_classes_json ['items']:
            if metric_class ['name'] == name:
                metric_class_json = metric_class
                break
        return metric_class_json

def collect():
    """
    Basic function for collection of metrics from UBNT routers, then upload results to NetIM
    """

    for Router in Routers:
	
        # Get InputMetricClassID
        metric_class_json2 = MetricClassesAPI (NetIMCoreServer, username=User, password=Password).get_metric_class_by_name (InputMetricClassName)
        InputMetricClassID = metric_class_json2 ['id']

		# Prepare output
        metric_class_json1 = MetricClassesAPI (NetIMCoreServer, username=User, password=Password).get_metric_class_by_name (OutputMetricClassName)
        device_json = DevicesAPI (NetIMCoreServer, username=User, password=Password).get_device_by_name (Router)
        tstamp = '%s000' % int (datetime.now ().timestamp ())
        metric_data_json1 = METRIC_DATA_TEMPLATE
        metric_data_json1 ['identifiers']['VNES_OE']['deviceID'] = device_json ['deviceAccessInfoId']
        metric_data_json1 ['metricClass'] = metric_class_json1 ['id']
        metric_data_json1 ['maxTimestamp'] = tstamp
        metric_data_json1 ['minTimestamp'] = tstamp
        metric_data_json1 ['sampleList'].clear()

        "Get the element IDs of each Router"
        Devicelist = requests.get('https://' + NetIMCoreServer + ':' + NetIMCoreServerPort + '/api/netim/v1/devices', auth=(User,Password), verify=False).json()["items"]
        RouterID=""
        for Device in Devicelist:
            if Device["name"] == Router:
                RouterID = Device["id"]

        "Get time stamps for interval"
        endTime = str(time.time()).split('.')[0] + '000'
        startTime = str(int(str(time.time()).split('.')[0]) - Interval) + '000'

        "Query the polled route table"
        jsondict = requests.get('https://' + NetIMCoreServer + ':' + NetIMCoreServerPort + '/swarm/NETIM_NETWORK_METRIC_DATA_SERVICE/api/v1/network-metric-data?elementIds=' \
        + RouterID + '&elementType=VNES_OE&endTime=' + endTime + '&metricClass=' + InputMetricClassID +'&startTime=' + startTime, \
        auth=(User,Password), verify=False).json()

        "Find BGP routes younger than interval, insert into json list"
        metricElementDataList = jsondict["metricData"]["metricElementDataList"]
        for metricElementData in metricElementDataList:	
            ElementId = metricElementData["elementId"]
            ValueList = metricElementData["timestampToValuesMap"]	
            Lastkey = sorted(ValueList.keys())[-1]
            Protocol = str(int(ValueList[Lastkey][0]))
            ProtocolInt = int(ValueList[Lastkey][0])	
            Age = ValueList[Lastkey][1]
            if Protocol == "14" and Age < Interval:			
                elementIdToObjectInfoMap = jsondict["elementIdToObjectInfoMap"]	
                keys = elementIdToObjectInfoMap.keys()
                for key in keys:
                    if str(key) == str(ElementId):				
                        Destination = str(elementIdToObjectInfoMap[key]["ipCidrRouteDest"])
                        Mask = str(elementIdToObjectInfoMap[key]["ipCidrRouteMask"])
                        CIDR = str(sum(bin(int(x)).count('1') for x in Mask.split('.')))
                        NextHop = str(elementIdToObjectInfoMap[key]["ipCidrRouteNextHop"])
                        DCN = Destination + " - " + CIDR + " - " + NextHop
                        sample_json1 = {
						'sampleInfo': None,
						'fieldValues': {
						'DCN': DCN,
						'Flap': 1,
						'Protocol': ProtocolInt,		
						'timestamp': tstamp
								}
						}
                        metric_data_json1 ['sampleList'].append (sample_json1)

        "If any new routes then Inject into NetIM using REST API based on the Output UDM"
				
        if len(metric_data_json1 ['sampleList']) > 0:
            print (json.dumps (metric_data_json1, indent=2))
            NetworkMetricImportAPI (NetIMCoreServer, username=User, password=Password).import_metric (metric_data_json1)

        """
		"else if no new routes inject message indicating no new routes"
	
		else:
			sample_json1 = {
			'sampleInfo': None,
			'fieldValues': {
			'DCN': "Polls with no changes",
			'Flap': 0,
			'Protocol': 0,		
			'timestamp': tstamp
				}
			}
			metric_data_json1 ['sampleList'].append (sample_json1)
			print (json.dumps (metric_data_json1, indent=2))
			NetworkMetricImportAPI (NetIMCoreServer, username=User, password=Password).import_metric (metric_data_json1)
		"""		


			
if __name__ == '__main__':
	collect()