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
from setuptools import find_packages, setup
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_exec

setup(
    name="ci_exec",
    version=ci_exec.__version__,
    packages=find_packages(exclude=["testing", "testing.*"]),
    zip_safe=True,
    url="https://github.com/svenevs/ci_exec"
)
