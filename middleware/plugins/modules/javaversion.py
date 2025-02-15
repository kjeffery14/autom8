#!/usr/bin/python
# middleware/plugins/modules/javaversion.py
# @version v2025.2.13.0
# @author Kevin Jeffery

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]
import os

class javaversion:
  def __init__(self, module):
    self.module = module
    self.module.debug("*** Process all Arguments")
    self.java_home  = self.module.params['java_home']
    self.executable = '{java_home}/bin/java',format(java_home=self.java_home)
  
  def version(self):
    data = dict(version='none', installed=False)
    if os.path.exists(self.executable):
      data['installed'] = True
      stderr = self._run_command('-version')[2]
      stderr_lines = stderr.split('\n')
      for line in stderr_lines:
        parts = line.split(' ')
        if line.startswith('java version'):
          data['version'] = parts[2].replace('"', '').replace('-', '.').replace('_','.')
          continue
        if line.startswith('Eclipse OpenJ9 VM'):
          data['version'] = parts[3].replace('"', '').replace('-', '.').replace('_','.')
          continue
        if line.startswith('Java(TM)') or line.startswith('IBM Semeru'):
          data['name'] = line
          continue
        if line.startswith('Java HotSpot'):
          data['hotspot'] = line
    self.module.exit_json(changed=False, data=data)
  
  def _run_command(self, params):
    cmd = '{0} {1}'.format(self.executable, params)
    rc, stdout, stderr = self.module.run_command(cmd)
    if rc > 0:
      self.module.fail_json(changed=False, msg=f'javaversion: {params}', rc=rc, stdout=stdout, stderr=stderr)
    return rc, stdout, stderr

def main():
  module = AnsibleModule(
    argument_spec=dict(
      java_home=dict(required=True, type='str')
    ),
    supports_check_mode=False
  )
  inst = javaversion(module)
  inst.version()

if __name__ == '__main__':
    main()
