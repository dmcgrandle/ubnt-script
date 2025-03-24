#/**********************************/
#/*       Copyright (c) 2020       */
#/*   Riverbed Technology, Inc.    */
#/*      All Rights Reserved.      */
#/**********************************/

import json
try:
    from .NetIMRESTAPIBase import NetIMRESTAPIBase
except ImportError:
    from NetIMRESTAPIBase import NetIMRESTAPIBase

# Use below as a template for post data
METRIC_DATA_TEMPLATE = {
   'source': 'poller',
   'metricClass': 'CPU_UTIL',
   'identifiers': {
      'VNES_OE': {
         'deviceID': '1552531610949'
      }
   },
   'maxTimestamp': 1554141300004,
   'minTimestamp': 1554141300004,
   'sampleList': [
       # Add list of samples as shown in SAMPLE_TEMPLATE
   ]
}

SAMPLE_TEMPLATE = {
    'sampleInfo': None,
    'fieldValues': {
        'cpuUtilType': 'cpmCPUTotal5minRev',
        'cpuUtil': '5.00',
        'cpuName': 'CPU of Routing Processor 5',
        'cpuIndex': '2016',
        'timestamp': '1554141300004'
    }
}

class NetworkMetricImportAPI (NetIMRESTAPIBase):
    def __init__ (self, server_address, protocol='https', port=8543, version='v1', username='admin', password='admin'):
        NetIMRESTAPIBase.__init__ (self, server_address, protocol, port, version, username, password)
        self.resource_url = self.base_url + '/swarm/NETIM_NETWORK_METRIC_IMPORT_SERVICE/api/v1/network-metric-import'

    def import_metric (self, data):
        return self.post_data (self.resource_url, data)

if __name__ == '__main__':
    o = NetworkMetricImportAPI ('10.46.250.210')
    o.import_metric (METRIC_DATA_TEMPLATE)
