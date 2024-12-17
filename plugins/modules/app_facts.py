#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Ladislav Cabelka <@ibt23sec5>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
module: app_facts

short_description:

version_added: 0.0.1

author: Ladislav Cabelka (@ibt23sec5)

attributes:
  check_mode:
    support: full
  diff_mode:
    support: none
  facts:
    support: full
  platform:
    platforms: posix
"""

EXAMPLES = r"""
"""

RETURN = r"""
ansible_facts:
  description: Facts to add to ansible_facts.
  returned: always
  type: complex
  contains:
    app:
      description: colection of specified or all defined subsets
      returned: always
      type: dict
      contains:
"""

from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule

from abc import ABC, abstractmethod

from ..module_utils.packages import get_files

class AppFacts(ABC):
    @abstractmethod
    def get(self):
        pass


class SSSDFacts(AppFacts):
    def get(self):


def main():
    module_args = dict(subsets=dict(type="list", elements="str"))

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    classes = [SSSDFacts,
               ]
    try:
        facts =
        result = dict(changed=False, ansible_facts={"app": facts})
    except Exception as exc:
        module.warn("Facts collection failed: %s" % (to_text(exc)))
        module.fail_json(msg=to_text(exc))

    if module.check_mode:
        module.exit_json(**result)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
