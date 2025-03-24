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

class MetricClassesAPI (NetIMRESTAPIBase):
    def __init__ (self, server_address, protocol='https', port=8543, version='v1', username='admin', password='admin'):
        NetIMRESTAPIBase.__init__ (self, server_address, protocol, port, version, username, password)
        # /metric-classes
        self.resource_url = self.api_url + '/metric-classes'

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

if __name__ == '__main__':
    o = MetricClassesAPI ('10.46.250.210')
    metric_class = o.get_metric_class_by_name ('NetIMContainerEntry')
    print (json.dumps (metric_class, indent=4))
