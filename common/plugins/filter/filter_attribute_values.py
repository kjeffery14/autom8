#!/usr/bin/python
# common/plugins/filters/filter_attribute_values.py
# @version v2025.11.12
# @author Kevin Jeffery
# Ansible filter plugin: filter_attribute_values
# Returns entries from a list of dictionaries where the value of a given
# attribute is present in a provided list of values.

from __future__ import (absolute_import, division, print_function)
from ansible.errors import AnsibleFilterError # type: ignore
__metaclass__ = type

class FilterModule(object):
    """Ansible filter plugin entry point."""

    def filters(self):
        return {
            'filter_attribute_values': self.filter_attribute_values,
        }

    def _get_nested_value(self, item, attribute):
        """Retrieve a nested attribute value from a dict using dot notation.

        Returns None if any part of the path is missing or if item is not a dict.
        """
        if not attribute:
            return None
        if not isinstance(item, dict):
            return None
        parts = attribute.split('.')
        val = item
        for p in parts:
            if not isinstance(val, dict) or p not in val:
                return None
            val = val[p]
        return val

    def filter_attribute_values(self, source_list, values_list, attribute='state'):
        """Filter a list of dictionaries.

        source_list: list of dicts to filter
        values_list: iterable of allowed values (can be a single value or string)
        attribute: attribute name (supports dot-notation for nested dicts)
          Defaults to 'state'

        Returns a new list with only those dicts from source_list where the
        attribute's value is contained in values_list.
        """
        # Basic validation
        if not source_list:
            return []

        # Normalize values_list to an iterable list (handle single scalar and strings)
        if values_list is None:
            raise AnsibleFilterError("values_list cannot be None")
        if isinstance(values_list, (str, bytes)) or not hasattr(values_list, '__iter__'):
            values_list = [values_list]

        # Try to use a set for efficient lookups when possible
        try:
            values_set = set(values_list)
        except TypeError:
            # Unhashable items in values_list (e.g. dicts); fall back to list membership
            values_set = list(values_list)

        result = []
        for item in source_list:
            if not isinstance(item, dict):
                # skip non-dict items
                continue
            val = self._get_nested_value(item, attribute)
            if val in values_set:
                result.append(item)

        return result
