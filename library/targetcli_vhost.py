#!/usr/bin/python

DOCUMENTATION = '''
---
module: targetcli_vhost
short_description: TargetCLI vHost target module
description:
     - module for handling vhost objects in targetcli ('/vhost').
version_added: "2.0"
options:
  wwn:
    description:
      - WWN of vhost target
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
define new vhost target and generate random wwn
- targetcli_vhost: wwn=''

define new vhost target
- targetcli_vhost: wwn=iqn.1994-05.com.redhat:data

remove existing target
- targetcli_vhost: wwn=iqn.1994-05.com.redhat:hell state=absent
'''

from distutils.spawn import find_executable
from uuid import uuid4

def main():
        module = AnsibleModule(
                argument_spec = dict(
                        wwn=dict(required=True),
                        state=dict(default="present", choices=['present', 'absent']),
                ),
                supports_check_mode=True
        )

        if not module.params['wwn'] and module.params['state'] == 'present':
            module.params['wwn'] = "naa.5001405" + uuid4().hex[-9:]

        state = module.params['state']

        if find_executable('targetcli') is None:
            module.fail_json(msg="'targetcli' executable not found. Install 'targetcli'.")

        result = {}
        
        try:
            rc, out, err = module.run_command("targetcli '/vhost/%(wwn)s/tpg1 status'" % module.params)
            if rc == 0 and state == 'present':
                result['changed'] = False
            elif rc == 0 and state == 'absent':
                if module.check_mode:
                    module.exit_json(changed=True, wwn_value=module.params['wwn'])
                else:
                    rc, out, err = module.run_command("targetcli '/vhost delete %(wwn)s'" % module.params)
                    if rc == 0:
                        module.exit_json(changed=True, wwn_value=module.params['wwn'])
                    else:
                        module.fail_json(msg="Failed to delete vHost object")
            elif state == 'absent':
                result['changed'] = False
            else:
                if module.check_mode:
                    module.exit_json(changed=True, wwn_value=module.params['wwn'])
                else:
                    rc, out, err = module.run_command("targetcli '/vhost create %(wwn)s'" % module.params)
                    if rc == 0:
                        module.exit_json(changed=True, wwn_value=module.params['wwn'])
                    else:
                        module.fail_json(msg="Failed to define vHost object")
        except OSError as e:
            module.fail_json(msg="Failed to check vHost object - %s" %(e) )
        module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
main()
