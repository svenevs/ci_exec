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
"""Tests for the :mod:`ci_exec.utils` module."""

from ci_exec.utils import merge_kwargs


def test_merge_kwargs():
    """Validate :func:`~ci_exec.utils.merge_kwargs` merges as expected."""
    def abc(a: int = 1, b: int = 2, c: int = 3):
        """Original function to customize."""
        return a + b + c

    def permute_assert(func, *, a, b, c):
        """Assert default values of a, b, and c are currect for func."""
        assert func(a=0, b=0, c=0) == 0

        assert func(b=0, c=0) == a
        assert func(a=0, c=0) == b
        assert func(a=0, b=0) == c

        assert func(c=0) == a + b
        assert func(b=0) == a + c
        assert func(a=0) == b + c

        assert func() == a + b + c

    # Validate the default values.
    permute_assert(abc, a=1, b=2, c=3)

    # Was this really necessary?  No.  Hehehe.  Python is so flexible though xD
    def manufacture(**outer_kwargs):
        """Create a custom override."""
        def custom(**kwargs):
            return abc(**merge_kwargs(outer_kwargs, kwargs))
        return custom

    custom_a = manufacture(a=4)
    custom_b = manufacture(b=5)
    custom_c = manufacture(c=6)
    permute_assert(custom_a, a=4, b=2, c=3)
    permute_assert(custom_b, a=1, b=5, c=3)
    permute_assert(custom_c, a=1, b=2, c=6)

    custom_ab = manufacture(a=7, b=8)
    custom_ac = manufacture(a=9, c=10)
    custom_bc = manufacture(b=11, c=12)
    permute_assert(custom_ab, a=7, b=8, c=3)
    permute_assert(custom_ac, a=9, b=2, c=10)
    permute_assert(custom_bc, a=1, b=11, c=12)

    custom_abc = manufacture(a=13, b=14, c=15)
    permute_assert(custom_abc, a=13, b=14, c=15)
