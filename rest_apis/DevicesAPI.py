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

class DevicesAPI (NetIMRESTAPIBase):
    def __init__ (self, server_address, protocol='https', port=8543, version='v1', username='admin', password='admin'):
        NetIMRESTAPIBase.__init__ (self, server_address, protocol, port, version, username, password)
        # /devices
        self.resource_url = self.api_url + '/devices'

    def get_all_devices (self, limit=1000, offset=0, device_ids=None, device_ip=None):
        'Get all devices'
        resource_url = '%s?limit=%s&offset=%s' % (self.resource_url, limit, offset)
        if device_ids:
            resource_url += '&deviceIds=%s' % device_ids
        if device_ip:
            resource_url += '&deviceIp=%s' % device_ip

        devices_json = self.get_json_from_resource (resource_url)
        return devices_json

    def get_device_by_id (self, device_id):
        'Get device by its device id'
        resource_url = '%s/%s' % (self.resource_url, device_id) 
        device_json = self.get_json_from_resource (resource_url)
        return device_json

    def get_device_by_name (self, device_name):
        'Get device by its name'
        # Get all devices
        devices_json = self.get_all_devices ()

        # Find the device with given device name. If not found, return None.
        device_json = None
        for device in devices_json ['items']:
            if device ['name'] == device_name:
                device_json = device
                break
        return device_json

if __name__ == '__main__':
    o = DevicesAPI ('10.46.251.125')
    #ret = o.get_all_devices ()
    #print (json.dumps (ret, indent=4))
    device = o.get_device_by_name ('PE2.nclab.nbttech.com')
    print (json.dumps (device, indent=4))
