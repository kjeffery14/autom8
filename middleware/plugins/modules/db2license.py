#!/usr/bin/python
# middleware/plugins/modules/db2license.py
# @version v2025.1.24
# @author Kevin Jeffery

from ansible.module_utils.basic import AnsibleModule # type: ignore[import]
import os

actions = ['add_feature', 'add_license', 'get', 'get_all', 'remove_license', 'version']
db2_license_ids = ['db2dec', 'db2std', 'db2ese']
components = [
  dict(key='name', startswith='Product name'),
  dict(key='type', startswith='License type'),
  dict(key='expiry', startswith='Expiry date'),
  dict(key='id', startswith='Product identifier'),
  dict(key='enforcement', startswith='Enforcement policy'),
  dict(key='version', startswith='Version information'),
  dict(key='memory', startswith='Max amount of memory'),
  dict(key='cores', startswith='Max number of cores'),
  dict(key='performance_management', startswith='IBM DB2 Performance Management'),
  dict(key='high_capacity', startswith='IBM DB2 OEM High Capacity')
]

class db2license:
  def __init__(self, module):
    self.module    = module
    self.db2licm   = 'adm/db2licm'
    self.db2ls     = 'install/db2ls'
    self.installed = False
    self.level     = 'none'
    self.fixpack   = ''
    self.special   = ''
    self.licenses = []
    # Process all Arguments
    self.action             = self.module.params['action']
    self.db2_home           = self.module.params['db2_home']
    self.feature            = self.module.params['feature']
    self.id                 = self.module.params['id']
    self.path               = self.module.params['path']
    if os.path.exists(self.db2_home):
      self.installed = True
      self._get_version()
      self._get_licenses()
  
  def add_feature(self):
    license = self._get_license(self.id)
    if license['id'] == 'none':
      self.module.fail_json(changed=False, msg='Cannot add feature, license not found: {0}'.format(self.id))
    if self.feature in license and license[self.feature] == 'Licensed':
      self.module.exit_json(changed=False, data=license)
    self._add(self.id, self.path)

  def add_license(self):
    license = self._get_license(self.id)
    if license['id'] == 'none' or license['expiry'] == 'Expired':
      self._add(self.id, self.path)
    self.module.exit_json(changed=False, data=license)
  
  def get(self):
    self.module.exit_json(changed=False, data=self._get_license(self.id))
  
  def get_all(self):
    self.module.exit_json(changed=False, data=self.licenses)
  
  def remove_license(self):
    license = self._get_license(self.id)
    if license['id'] == 'none' or license['expiry'] == 'Expired':
      self.module.exit_json(changed=False, data=license)
    self._remove(self.id)

  def version(self):
    data = dict(version = self.level, installed = self.installed)
    self.module.exit_json(changed=False, data=data)

  def _add(self, id, path):
    if not os.path.exists(path):
      self.module.fail_json(changed=False, msg='License file not found: {0}'.format(path))
    self._run_command(self.db2licm, ['-a {0}'.format(path)])
    self.module.exit_json(changed=True, data=dict(id=id, path=path), msg='License added: {0}'.format(path))
  
  def _get_license(self, id):
    reply = dict(id = 'none', expiry = 'Expired')
    for license in self.licenses:
      if license['id'] == id:
        return license
    return reply
    
  def _get_licenses(self):
    stdout = self._run_command(self.db2licm, ['-l'])[1]
    license = {}
    isLicense = False
    for line in self._get_output_lines(stdout):
      if line.startswith('Product name'):
        if isLicense:
          self.licenses.append(license)
          license = {}
        isLicense = True
      license = self._process_output_line(line, license)
    if isLicense:
        self.licenses.append(license)

  def _get_version(self):
    stdout = self._run_command(self.db2ls, ['-q -p'])[1]
    for line in self._get_output_lines(stdout):
      if line.startswith(self.db2_home):
        parts = line.split()
        self.level = parts[1]
        self.fixpack = parts[2]
        if parts[3].isnumeric():
          self.special = parts[3]

  def _get_output_lines(self, output):
    return output.split('\n')
  
  def _process_output_line(self, line, license):
    parts = line.replace('"', '').split(':')
    if len(parts) > 1:
      value = parts[1].strip()
    else:
      return license
    for component in components:
      if line.startswith(component['startswith']):
        license[component['key']] = value
        break
    return license
    
  def _remove(self, id):
    self._run_command(self.db2licm, ['-r {0}'.format(id)])
    self.module.exit_json(changed=True, data=dict(id=id))
  
  def _run_command(self, cmd, params):
    cmd = '{0}/{1} {2}'.format(self.db2_home, cmd, ' '.join(params))
    rc, stdout, stderr = self.module.run_command(cmd, use_unsafe_shell=True)
    if rc > 0:
      self.module.fail_json(changed=False, msg='Command failed: {0} {1}'.format(cmd, ' '.join(params)), rc=rc, stdout=stdout, stderr=stderr)
    return rc, stdout, stderr

def main():
  module = AnsibleModule(
    argument_spec=dict(
      action = dict(required=True, type='str', choices=actions),
      db2_home = dict(required=True, type='str'),
      feature = dict(required=False, type='str', choices=['high_capacity', 'performance_management']),
      id = dict(required=False, type='str', choices=db2_license_ids),
      path = dict(required=False, type='str')
    ),
    required_if = [
      ('action', 'add_feature', ('feature', 'id', 'path')),
      ('action', 'add_license', ('id', 'path')),
      ('action', 'get', ('db2_home', 'id')),
      ('action', 'remove_license', ('db2_home', 'id'))
    ],
    supports_check_mode=False
  )

  module.debug('Started db2license module')
  inst = db2license(module)
  if inst.action == 'add_feature':
    inst.add_feature()
  if inst.action == 'add_license':
    inst.add_license()
  if inst.action == 'get':
    inst.get()
  if inst.action == 'get_all':
    inst.get_all()
  if inst.action == 'remove_license':
    inst.remove_license()
  if inst.action == 'version':
    inst.version()
  
  module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(inst.action))

if __name__ == '__main__':
    main()
