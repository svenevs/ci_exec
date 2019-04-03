# noqa: D100
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup ------------------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

this_file_dir = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(this_file_dir))
sys.path.insert(0, root)
import ci_exec  # noqa: E402


# -- Project information ---------------------------------------------------------------
project = "ci_exec"
copyright = "2019, Stephen McDowell"
author = "Stephen McDowell"

# The full version, including alpha/beta/rc tags
release = ci_exec.__version__


# -- General configuration -------------------------------------------------------------
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named "sphinx.ext.*") or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["venv"]


# -- Options for HTML output -----------------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]


# -- Extension setup -------------------------------------------------------------------
autodoc_member_order = "bysource"

intersphinx_mapping = {
    "python": ("http://docs.python.org/", None)
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True


def setup(app):  # noqa: D103
    app.add_css_file("custom.css")
