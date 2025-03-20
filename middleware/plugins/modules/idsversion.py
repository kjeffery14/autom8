#!/usr/bin/python
# middleware/plugins/modules/idsversion.py
# @version v1.00_2025-MAR-19
# @author Kevin Jeffery

import os
from ansible.module_utils.basic import AnsibleModule # type: ignore

major_versions = ['10.0.3', '10.0.2', '10.0.1', '10.0', '6.4', '6.3.1', '6.3']

class IDSVersion:
  def __init__(self, module):
    self.module = module
    self.module.debug("*** Process all Arguments")
    self.version = self.module.params['version']
    self.logLevel = self.module.params['log']
    self.ldaphome = self.module.params['ldaphome']

  def get_version(self):
    data, warnings = self._get_version_info(compare_version=self.version)
    self.module.exit_json(changed=False, data=data, warnings=warnings)

  def _get_major_version(self, version):
    for major_version in major_versions:
      if version.startswith(major_version):
        return major_version
    return 'n.a.'
  
  def _get_version_info(self, compare_version=None):
    data = dict(installed=False, version='0.0.0.0', installed_versions=[])
    warnings = []
    if os.path.exists(self.ldaphome) is False:
      return data, warnings
    data['installed'] = True
    stdout = self.module.run_command(self.ldaphome + '/bin/idsversion')[1]
    stdout_lines = stdout.split('\n')
    current_major = self.ldaphome.split('V')[1]
    for line in stdout_lines:
      if line.startswith('64-bit TDS server version:'):
        version = line.split(':')[1]
        major_version = self._get_major_version(version)
        version_info = dict(version = version, major_version = major_version)
        data['installed_versions'].append(version_info)
        if current_major == major_version:
          data['version'] = version
          data['major_version'] = major_version
    if compare_version is not None:
      compare_major = self._get_major_version(compare_version)
      if current_major != compare_major:
        data['is_upgrade'] = True
      elif current_major == compare_major and data['version'] != compare_version:
        data['is_fixpack'] = True
    else:
      warnings.append('No version to compare with')
    return data, warnings
  
  def _run_command(self, cmd):
    rc, stdout, stderr = self.module.run_command(cmd)
    if rc > 0:
      self.module.fail_json(changed=False, msg='Unable to get version', stderr=stderr, rc=rc, stdout=stdout)
    return rc, stdout, stderr

  def _version_compare(self, current_version, compare_version):
    current_components = current_version.split('.')
    compare_components = compare_version.split('.')
    reply = {'is_upgrade': False, 'is_update': False, 'is_fixpack': False}
    if current_components[0] < compare_components[0] or (current_components[0] == compare_components[0] and current_components[1] < compare_components[1]):
      reply.is_upgrade = True
    elif current_components[3] < compare_components[3]:
      reply.is_update = True
    elif len(compare_components) > 3:
      if len(current_version) < 4:
        reply.is_fixpack = True
      elif current_components[4] < compare_components[4]:
        reply.is_fixpack = True
    return reply  

def main():
  module = AnsibleModule(
    argument_spec=dict(
      version = dict(required=False, type='str'),
      log=dict(required=False, type='str', default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
      ldaphome=dict(required=True, type='str')
    ),
    supports_check_mode=False
  )

  module.debug('Started idsversion module')
  
  inst = IDSVersion(module)
  inst.get_version()

if __name__ == '__main__':
  main()
