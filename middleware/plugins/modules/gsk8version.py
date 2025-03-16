#!/usr/bin/python
# middleware/plugins/modules/gsk8version.py
# @version v2025.3.16.0
# @author Kevin Jeffery

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]
import os
from sys import version_info


class gsk8version:
  def __init__(self, module):
    self.executable = None
    self.module = module
    self.module.debug("*** Process all Arguments")
    self.installed        = False
    self.platform         = self.module.params['platform']
    if self.platform == 'LinuxX64':
      self.executable = '/usr/bin/gsk8capicmd_64'
    if self.executable is not None and os.path.exists(self.executable):
      self.installed = True
    self.version          = self.module.params['version']
    if self.version is not None:
      components = self.version.split('.')
      if len(components) == 4:
        self.name = '{0}-ISS-GSKIT-{1}-FP00{2}'.format(self.version, self.platform, components[3])
      else:
        self.name = None

  def get_version(self):
    data = dict(version='0.0.0.0', installed=self.installed, upgrade=False)
    warnings = []
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
    if self.version is not None:
      if self.name is None:
        warnings.append('version does not have four components')
      else:
        data['name'] = self.name
        data['archive'] = '{0}.tar.gz'.format(self.name)
        if self.platform == 'LinuxX64':
          data['packages'] = [
            "32/gskcrypt32-{0}.linux.x86.rpm".format(self.version),
            "32/gskssl32-{0}.linux.x86.rpm".format(self.version),
            "64/gskcrypt64-{0}.linux.x86_64.rpm".format(self.version),
            "64/gskssl64-{0}.linux.x86_64.rpm".format(self.version)
          ]
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
      platform=dict(required=False, type='str', default='LinuxX64', choices=['LinuxX64']),
      version=dict(required=False, type='str')
    ),
    supports_check_mode=False
  )

  module.debug('Started gsk8version module')
  if version_info.major < 3:
    module.fail_json(changed=False, msg='Python3 is required on executing host')

  inst = gsk8version(module)
  inst.get_version()

if __name__ == '__main__':
    main()
