#/**********************************/
#/*       Copyright (c) 2021       */
#/*   Riverbed Technology, Inc.    */
#/*      All Rights Reserved.      */
#/**********************************/

import sys
sys.path.append('/home/netimadmin/Riverbed/TE/3.1.4/TestEngine/service/linux/bin')
from rest_apis.DevicesAPI import DevicesAPI
from rest_apis.MetricClassesAPI import MetricClassesAPI
from rest_apis.NetworkMetricImportAPI import NetworkMetricImportAPI, METRIC_DATA_TEMPLATE
from datetime import datetime
import json
import socket
import subprocess
import re
import random
import time
import requests
import json
import time

"Silently skip certificate verification warning"
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


##################### CONFIGURATION ##################

"Access to NetIM Server"
NetIMCoreServer = '10.99.31.75'
NetIMCoreServerPort = '8543'

"NetIM API credentials"
User = 'admin'
Password = 'admin'

"Routers"
Routers = ['n21-rtr.cyberdyne.corp', 'n31-rtr.cyberdyne.corp']

"Input UDM"
InputMetricClassName = 'Route-Table'

"Output UDM"
OutputMetricClassName = 'Route-Changes'

"Frequency to be aligned with polling frequency of the input UDM (above)"
Interval = 300

##################### CONFIGURATION ##################


def collect():

	for Router in Routers:
	
		"Get InputMetricClassID"	
		metric_class_json2 = MetricClassesAPI (NetIMCoreServer, username=User, password=Password).get_metric_class_by_name (InputMetricClassName)
		InputMetricClassID = metric_class_json2 ['id']

		"Prepare output"
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