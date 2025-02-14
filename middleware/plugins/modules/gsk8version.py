#!/usr/bin/python
# middleware/plugins/modules/gsk8version.py
# @version v2025.2.13.1
# @author Kevin Jeffery

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]
import os
from sys import version_info


class gsk8version:
  def __init__(self, module):
    self.module = module
    self.executable = '/usr/bin/gsk8capicmd_64'
    self.module.debug("*** Process all Arguments")
    self.installed        = os.path.exists(self.executable)

  def version(self):
    data = dict(version='none', installed=self.installed)
    if self.installed:
      stdout = self._run_command(['-version'])[1]
      for line in stdout.split('\n'):
        if line.startswith('@(#)'):
          line = line.replace('@(#)', '')
          parts = line.split(':')
        else:
          continue
        if line.startswith('FileDescription'):
          data['description'] = parts[1].strip()
          continue
        if line.startswith('FileVersion'):
          data['version'] = parts[1].strip()
          continue
        if line.startswith('InternalName'):
          data['name'] = parts[1].strip()
          continue
        if line.startswith('ProductName'):
          data['build'] = parts[1].strip()
    self.module.exit_json(changed=False, data=data)
  
  def _run_command(self, params):
    param_string = ' '.join(params)
    cmd = f'{self.executable} {param_string}'
    rc, stdout, stderr = self.module.run_command(cmd)
    if rc > 0:
      self.module.fail_json(changed=False, msg=f'gsk8ver: {param_string}', rc=rc, stdout=stdout, stderr=stderr)
    return rc, stdout, stderr

def main():
  module = AnsibleModule(
    argument_spec=dict(
      log=dict(required=False, type='str', default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
    ),
    supports_check_mode=False
  )

  module.debug('Started gsk8version module')
  if version_info.major < 3:
    module.fail_json(changed=False, msg='Python3 is required on executing host')

  inst = gsk8version(module)
  inst.version()

if __name__ == '__main__':
    main()
