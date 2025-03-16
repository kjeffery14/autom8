#!/usr/bin/python
# middleware/plugins/modules/javaversion.py
# @version v2025.3.16.0
# @author Kevin Jeffery

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]
import os

class javaversion:
  def __init__(self, module):
    self.module = module
    self.module.debug("*** Process all Arguments")
    self.java_home  = self.module.params['java_home']
    self.platform   = self.module.params['platform']
    self.version    = self.module.params['version']
    if self.version is not None:
      components = self.version.split('.')
      if len(components) == 4:
        self.archive = '{0}-ISS-JAVA-{1}-FP00{2}.tar'.format(self.version, self.platform, components[3])
      else:
        self.archive = None
    if self.platform == 'LinuxX86':
      self.executable = '{java_home}/bin/java'.format(java_home=self.java_home)
  
  def get_version(self):
    data = dict(version='0.0.0.0', installed=False, upgrade=False)
    warnings = []
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
    if self.version is not None:
      if self.archive is None:
        warnings.append('version does not have four components')
      else:
        data['archive'] = self.archive
        if self.installed and data['version'] is not None:
          want_version = self.version.split('.')
          have_version = data['version'].split('.')
          for i in range(4):
            if int(have_version[i]) < int(want_version[i]):
              warnings.append('installed version is less than requested version')
              data['upgrade'] = True
              break
    self.module.exit_json(changed=False, data=data, warnings=warnings)
  
  def _run_command(self, params):
    cmd = '{0} {1}'.format(self.executable, params)
    rc, stdout, stderr = self.module.run_command(cmd)
    if rc > 0:
      self.module.fail_json(changed=False, msg=f'javaversion: {params}', rc=rc, stdout=stdout, stderr=stderr)
    return rc, stdout, stderr

def main():
  module = AnsibleModule(
    argument_spec=dict(
      java_home=dict(required=True, type='str'),
      platform=dict(required=False, type='str', default='LinuxX64', choices=['LinuxX64']),
      version=dict(required=False, type='str')
    ),
    supports_check_mode=False
  )
  inst = javaversion(module)
  inst.get_version()

if __name__ == '__main__':
    main()
