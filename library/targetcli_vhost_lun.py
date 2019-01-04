#!/usr/bin/python

DOCUMENTATION = '''
---
module: targetcli_vhost_lun
short_description: TargetCLI LUN module for vHost targets
description:
     - module for handling vHost LUN objects in targetcli ('/vhost/.../tpg1/luns').
version_added: "2.0"
options:
  wwn:
    description:
      - WWN of vHost target (server)
    required: true
    default: null
  backstore_type:
    description:
      - type of backstore object
    required: true
    default: null
  backstore_name:
    description:
      - name of backstore object
    required: true
    default: null
  state:
    description:
      - Should the object be present or absent from TargetCLI configuration
    required: false
    default: present
    choices: [present, absent]
notes:
   - Tested on CentOS 7.2
requirements: [ ]
author:
    - "Ondrej Famera <ondrej-xa2iel8u@famera.cz>"
    - "George Diamantopoulos <georgediam@gmail.com>"
'''

EXAMPLES = '''
define new vHost LUN
- targetcli_vhost_lun: wwn=iqn.1994-05.com.redhat:fastvm backstopre_type=block backstore_name=test1

remove vHost LUN
- targetcli_vhost_lun: wwn=iqn.1994-05.com.redhat:hell backstopre_type=block backstore_name=test2 state=absent
'''

from distutils.spawn import find_executable

def main():
        module = AnsibleModule(
                argument_spec = dict(
                        wwn=dict(required=True),
                        backstore_type=dict(required=True),
                        backstore_name=dict(required=True),
                        state=dict(default="present", choices=['present', 'absent']),
                ),
                supports_check_mode=True
        )

        lun_path = module.params['backstore_type']+"/"+module.params['backstore_name']
        state = module.params['state']

        result = {}
        luns = {}
        
        try:
            # check if the vhost target exists
            rc, out, err = module.run_command("targetcli '/vhost/%(wwn)s/tpg1 status'" % module.params)
            if rc != 0 and state == 'present':
                result['changed'] = False
                module.fail_json(msg="vHost object doesn't exist")
            elif rc != 0 and state == 'absent':
                result['changed'] = False
                # ok vHost object doesn't exist so LUN is also not there --> success 
            else:
                # lets parse the list of LUNs from the targetcli
                rc, output, err = module.run_command("targetcli '/vhost/%(wwn)s/tpg1/luns ls'" % module.params)
                for row in output.split('\n'):
                    row_data = row.split(' ')
                    if len(row_data) < 2 or row_data[0] == 'luns':
                        continue
                    if row_data[1] == "luns":
                        continue
                    luns[row_data[5][1:]] = row_data[3][3:]
                if state == 'present' and luns.has_key(lun_path):
                    # LUN is already there and present
                    result['changed'] = False
                    result['lun_id'] = luns[lun_path]
                elif state == 'absent' and not luns.has_key(lun_path):
                    # LUN is not there and should not be there
                    result['changed'] = False
                elif state == 'present' and not luns.has_key(lun_path):
                    # create LUN
                    if module.check_mode:
                        module.exit_json(changed=True)
                    else:
                        rc, out, err = module.run_command("targetcli '/vhost/%(wwn)s/tpg1/luns create /backstores/%(backstore_type)s/%(backstore_name)s'" % module.params)
                        if rc == 0:
                            module.exit_json(changed=True)
                        else:
                            module.fail_json(msg="Failed to create vHost LUN object")

                elif state == 'absent' and luns.has_key(lun_path):
                    # delete LUN
                    if module.check_mode:
                        module.exit_json(changed=True)
                    else:
                        rc, out, err = module.run_command("targetcli '/vhost/%(wwn)s/tpg1/luns delete lun" % module.params + luns[lun_path] + "'")
                        if rc == 0:
                            module.exit_json(changed=True)
                        else:
                            module.fail_json(msg="Failed to delete vHost LUN object")
        except OSError as e:
            module.fail_json(msg="Failed to check vHost lun object - %s" %(e) )
        module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
