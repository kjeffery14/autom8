#!/usr/bin/python
# middleware/plugins/modules/basic_module.py
# @version v2025.2.8
# @author Kevin Jeffery
# @see https://techdocs.broadcom.com/us/en/vmware-cis/desktop-hypervisors/workstation-pro/17-0/use-the-vmware-workstation-player-rest-api-service.html
# @see https://github.com/ecthros/vrest

import requests
import base64
import json

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]

actions = [
    'version', # Module version
    'get_vms'  # VM Information
]
class vwsrest:
    def __init__(self, module):
        self.module = module
        self.module.debug("*** Process all Arguments")
        self.action             = self.module.params['action']
        self.baseurl            = self.module.params['baseurl']
        self.force              = self.module.params['force']
        self.logLevel           = self.module.params['log']
        self.password           = self.module.params['password']
        self.username           = self.module.params['username']
        self.version            = '2025.2.8'
        self.headers = {
            "Authorization": "Basic {authentication_string}".format(authentication_string=base64.b64encode(f"{self.username}:{self.password}")), 
            "Content-type": "application/vnd.vmware.vmw.rest-v1+json", 
            "Accept": "application/vnd.vmware.vmw.rest-v1+json"
        }

    def get_vms(self):
        http_status, vmlist, warnings = self._rest_request('GET', f"{self.baseurl}/vms")
        data = dict()
        for vm in vmlist:
            vmid = vm['id']
            vmpath = vm['path']
            vminfo = self._rest_request('GET', f"{self.baseurl}/vms/{vmid}/restictions", warnings=warnings)[1]
            data[vmid] = vminfo
            data[vmid]['path'] = vmpath
        self.module.exit_json(changed=False, data=data, http_status=http_status, warnings=warnings)

    def get_version(self):
        self.module.exit_json(changed=False, data=self.version)
    
    def _check_response(self, response, fail_on_error=True, warnings=[]):
        data = None
        if response.status_code == 401:
            warnings.append("Authentication required")
        elif response.status_code == 200:
            if self.logLevel == 'DEBUG': warnings.append("Request successful.")
        elif response.status_code == 204:
            if self.logLevel == 'DEBUG': warnings.append("Request successful, no output")
        else:
            warnings.append(f"HTTP Status {response.status_code}")
        if response.content:
            data = json.loads(response.content.decode("ascii"))
        if fail_on_error and response.status_code >= 300:
            self.module.fail_json(changed=False, data=data, http_status=response.status_code, msg=warnings[0], warnings=warnings)    
        return response.status_code, data, warnings

    def _rest_request(self, method, url, json=None, params=None, warnings=[]):
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, json=json, headers=self.headers)
            elif method == 'PATCH':
                response = requests.patch(url, params=params)
            else:
                msg = f"Invalid method: {method} URL: {url}"
                warnings.append(msg)
                self.module.fail_json(changed=False, msg=msg, warnings=warnings)
        except requests.exceptions.RequestException as e:
            warnings.append(e)
            self.module.fail_json(changed=False, msg=e, warnings=warnings)
        return self._check_response(response, warnings=warnings)

    
def main():
    module = AnsibleModule(
        argument_spec=dict(
        action=dict(required=True, type='str', choices=actions),
        baseurl=dict(required=True, type='str'),     
        force=dict(required=False, default=False, type='bool'),
        log=dict(required=False, default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
        password=dict(required=True, type='str', no_log=True),
        username=dict(required=True, type='str')
       ),
        # required_together=[['required1', 'required2']],
        # required_if [('argument', 'value', ('required1', 'required2'))],
        supports_check_mode=False
   )

    module.debug('Started module')

    inst = vwsrest(module)

    if inst.action == "version":
        inst.get_version()
    if inst.action == "get_vms":
        inst.get_vms

    module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(inst.action))


if __name__ == '__main__':
    main()
