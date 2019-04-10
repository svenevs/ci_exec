########################################################################################
# Copyright 2019 Stephen McDowell                                                      #
#                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                      #
# you may not use this file except in compliance with the License.                     #
# You may obtain a copy of the License at                                              #
#                                                                                      #
#     http://www.apache.org/licenses/LICENSE-2.0                                       #
#                                                                                      #
# Unless required by applicable law or agreed to in writing, software                  #
# distributed under the License is distributed on an "AS IS" BASIS,                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.             #
# See the License for the specific language governing permissions and                  #
# limitations under the License.                                                       #
########################################################################################
"""
Assorted utility functions.

This module aims to house any utility functions that may facilitate easier consumption
of the ``ci_exec`` package.
"""


def merge_kwargs(defaults: dict, kwargs: dict):
    """
    Merge ``defaults`` into ``kwargs`` and return ``kwargs``.

    Intended usage is for setting defaults to ``**kwargs`` when the caller did not
    provide a given argument, but making sure not to overwrite the caller's explicit
    argument when specified.

    For example::

        >>> merge_kwargs({"a": 1, "b": 2}, {})
        {'a': 1, 'b': 2}
        >>> merge_kwargs({"a": 1, "b": 2}, {"a": 3})
        {'a': 3, 'b': 2}

    Entries in the ``defaults`` parameter only get included of **not** present in the
    ``kwargs`` argument.  This is to facilitate something like this::

        from ci_exec import merge_kwargs

        # The function we want to customize the defaults for.
        def func(alpha=1, beta=2):
            return alpha + beta

        # Example: default to alpha=2, leave beta alone.
        def custom(**kwargs):
            return func(**merge_kwargs({"alpha": 2}, kwargs))

        # custom()                == 4
        # custom(alpha=0)         == 2
        # custom(beta=0)          == 2
        # custom(alpha=0, beta=0) == 0

    Parameters
    ----------
    defaults : dict
        The dictionary of defaults to add to ``kwargs`` if not present.

    kwargs : dict
        The dictionary to merge ``defaults`` into.

    Return
    ------
    dict
        The ``kwargs`` dictionary, possibly with values from ``defaults`` injected.
    """
    for key, val in defaults.items():
        if key not in kwargs:
            kwargs[key] = val

    return kwargs
