# Copyright 2013-2020 Intranet AG and contributors
#
# avocado-i2n is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# avocado-i2n is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with avocado-i2n.  If not, see <http://www.gnu.org/licenses/>.

"""

SUMMARY
------------------------------------------------------
Utility for the main test suite substructures like test objects.

Copyright: Intra2net AG


INTERFACE
------------------------------------------------------

"""

import logging

from .. import params_parser as param


class TestObject(object):
    """A wrapper for a test object used in one or more test nodes."""

    def params(self):
        """Parameters (cache) property."""
        if self._params_cache is None:
            self.regenerate_params()
        return self._params_cache
    params = property(fget=params)

    def final_restr(self):
        """Final restriction to make the object parsing variant unique."""
        return self.config.steps[-1].parsable_form()
    final_restr = property(fget=final_restr)

    def long_suffix(self):
        """Sufficiently unique suffix to identify a variantless test object."""
        return self._long_suffix
    long_suffix = property(fget=long_suffix)

    def id(self):
        """Unique ID to identify a test object."""
        return self.long_suffix + "-" + self.params["name"]
    id = property(fget=id)

    def __init__(self, suffix, config):
        """
        Construct a test object (vm) for any test nodes (tests).

        :param str name: name of the test object
        :param config: variant configuration for the test object
        :type config: :py:class:`param.Reparsable`
        """
        self.suffix = suffix.split("_")[0]
        self._long_suffix = suffix
        self.config = config
        self._params_cache = None

        # TODO: integrate these features better
        self.current_state = "unknown"

        self.composites = []
        self.components = []

    def __repr__(self):
        shortname = self.params.get("shortname", "<unknown>")
        return f"[object] longsuffix='{self.long_suffix}', shortname='{shortname}'"

    def is_permanent(self):
        """
        If the test object is permanent, it can only be created manually
        (possibly through the use of manual setup steps).

        On states on permanent test object are treated differently than
        on states on normal test object since they are preserved through
        test runs and even host shutdowns.
        """
        return self.params.get("permanent_vm", "no") == "yes"

    def object_typed_params(self, params):
        """
        Return object and type filtered parameters using the current object type.

        :param params: whether to show generated parameter dictionaries
        :type params: :py:class:`param_utils.Params`
        """
        # TODO: we don't support recursion at the moment but this is fine
        # for the current implicit assumption of nets->vms->images
        for composite in self.composites:
            params = params.object_params(composite.suffix)
        return params.object_params(self.suffix).object_params(self.key)

    def regenerate_params(self, verbose=False):
        """
        Regenerate all parameters from the current reparsable config.

        :param bool verbose: whether to show generated parameter dictionaries
        """
        generic_params = self.config.get_params(show_dictionaries=verbose)
        self._params_cache = self.object_typed_params(generic_params)


class NetObject(TestObject):
    """A Net wrapper for a test object used in one or more test nodes."""

    def __init__(self, name, config):
        """
        Construct a test object (vm) for any test nodes (tests).

        All arguments are inherited from the base class.
        """
        super().__init__(name, config)
        self.key = "nets"
        self.components = []


class VMObject(TestObject):
    """A VM wrapper for a test object used in one or more test nodes."""

    def __init__(self, name, config):
        """
        Construct a test object (vm) for any test nodes (tests).

        All arguments are inherited from the base class.
        """
        super().__init__(name, config)
        self.key = "vms"
        self.components = []


class ImageObject(TestObject):
    """An image wrapper for a test object used in one or more test nodes."""

    def id(self):
        """Sufficiently unique ID to identify a test object."""
        assert len(self.composites) == 1, "Image objects need a unique composite"
        return self.long_suffix + "-" + self.composites[0].params["name"]
    id = property(fget=id)

    def __init__(self, name, config):
        """
        Construct a test object (vm) for any test nodes (tests).

        All arguments are inherited from the base class.
        """
        super().__init__(name, config)
        self.key = "images"
        self.params["main_vm"] = "none"
