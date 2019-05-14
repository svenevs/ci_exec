# noqa: D100
import os
import sys

from setuptools import find_packages, setup


if sys.version_info < (3, 5):
    raise RuntimeError("ci_exec needs Python 3.5+")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ci_exec  # noqa: E402, I100

# Extract the descriptions from README.rst.
try:
    in_brief = False
    brief = ""
    in_long = False
    in_final = False
    long = ""
    with open("README.rst") as readme:
        for line in readme:
            if line.startswith(".. begin_brief_desc"):
                in_brief = True
                continue
            elif line.startswith(".. end_brief_desc"):
                in_brief = False
                continue
            elif line.startswith(".. begin_long_desc"):
                in_long = True
                continue
            elif line.startswith(".. end_long_desc"):
                in_long = False
                continue
            elif line.startswith(".. begin_final_desc"):
                in_final = True
                continue
            elif line.startswith(".. end_final_desc"):
                in_final = False
                continue

            if in_brief:
                brief += line.replace("\n", " ")  # so it is all on one line.
            elif in_long:
                long += line
            elif in_final:
                long += line

    if not brief:
        raise RuntimeError("Internal error: could not extract brief description.")
    if not long:
        raise RuntimeError("Internal error: could not extract long description.")
except Exception as e:
    raise RuntimeError("CRITICAL: {e}".format(e=e))

brief_description = brief.rstrip()
long_description = long.rstrip()

setup(
    name="ci_exec",
    version=ci_exec.__version__,
    requires_python=">=3.5",
    author="Stephen McDowell",
    author_email="svenevs.pypi@gmail.com",
    license="Apache v2.0",
    description=brief_description,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    project_urls={
        "Documentation": "https://ci-exec.readthedocs.io/en/latest/",
        "Source": "https://github.com/svenevs/ci_exec"
    },
    url="https://github.com/svenevs/ci_exec",
    packages=find_packages(exclude=[
        "demos", "demos.*",
        "docs", "docs.*",
        "tests", "tests.*",
    ]),
    zip_safe=True,
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ]
)
