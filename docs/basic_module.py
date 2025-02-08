#!/usr/bin/python
# middleware/plugins/modules/basic_module.py
# @version v1.00_2025-FEB-08
# @author Kevin Jeffery

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]

actions = [
    'version' # Module version 
]
class basic_module:
    def __init__(self, module):
        self.module = module
        self.module.debug("*** Process all Arguments")
        self.logLevel           = self.module.params['log']
        self.force              = self.module.params['force']
        self.action             = self.module.params['action']
        self.version            = '2025.2.8'

    def get_version(self):
        self.module.exit_json(changed=False, data=self.version)
    
def main():
    module = AnsibleModule(
        argument_spec=dict(
        log=dict(required=False, default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
        force=dict(required=False, default=False, type='bool'),
        action=dict(required=True, type='str', choices=actions),        
       ),
        # required_together=[['required1', 'required2']],
        # required_if [('argument', 'value', ('required1', 'required2'))],
        supports_check_mode=False
   )

    module.debug('Started module')

    inst = basic_module(module)

    if inst.action == "version":
        inst.get_version()

    module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(inst.action))


if __name__ == '__main__':
    main()
