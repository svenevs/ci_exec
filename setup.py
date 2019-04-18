# noqa: D100
import os
import sys

from setuptools import find_packages, setup

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_exec  # noqa: E402, I100

setup(
    name="ci_exec",
    version=ci_exec.__version__,
    packages=find_packages(exclude=["tests", "tests.*", "demos", "demos.*"]),
    zip_safe=True,
    url="https://github.com/svenevs/ci_exec"
)
