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

from docutils.nodes import definition_list
from docutils.statemachine import StringList

from sphinx.ext.autosummary import Autosummary  # type: ignore


this_file_dir = os.path.dirname(os.path.abspath(__file__))
root = os.path.dirname(os.path.dirname(this_file_dir))
demos = os.path.join(root, "demos")
sys.path.insert(0, root)
sys.path.insert(1, demos)
import ci_exec  # noqa: E402, I100


sys.path.insert(0, os.path.join(this_file_dir, "_extensions"))
from youtube import Youtube, YoutubeDirective, depart_youtube_node, visit_youtube_node  # noqa: E402, E501


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


class DefinitionListSummary(Autosummary):
    """Hack around autosummary to enumerate as definition list rather than a table."""

    def get_table(self, items):
        """Return a definition list rather than a table."""
        # See original implementation:
        # https://github.com/sphinx-doc/sphinx/blob/master/sphinx/ext/autosummary/__init__.py
        source, line = self.state_machine.get_source_and_line()
        src = "{source}:{line}:<dlistsummary>".format(source=source, line=line)

        # We're going to build out a StringList by formatting a definition list and then
        # parsing it at the end.  Definition list syntax:
        #
        # **First Item**
        #     First item description, indented by four spaces.
        # **Second Item**
        #     Second item description, indented by four spaces.
        s_list = StringList()
        for name, signature, summary_string, real_name in items:
            # Add the definition item.
            s_list.append("**{name}**\n".format(name=name), src)

            # Add the autosummary description for this demo, including a link to the
            # full demonstration.  This is the definition of the item.
            summary_string += "  :any:`Go to demo ↱ <{real_name}>`\n".format(
                real_name=real_name
            )
            s_list.append("    " + summary_string, src)

        # Now that we have a fully populated StringList, let Sphinx handle the dirty
        # work of evaluating the rst as actual nodes.
        node = definition_list("")
        self.state.nested_parse(s_list, 0, node)
        try:
            if isinstance(node[0], definition_list):
                node = node[0]
        except IndexError:
            pass

        return [node]


class ProviderSummary(Autosummary):
    """Generate an autosummary table for ci_exec.utils.Provider automatically."""

    def get_items(self, names):
        """Return parent class ``get_items`` with dynamic ``names`` list."""
        all_providers = []
        for key, val in ci_exec.Provider.__dict__.items():
            if key.startswith("is_"):
                # Use the fully qualified name here so Sphinx finds it.
                # (avoid need to use .. currentmodule:: in docstring)
                all_providers.append("ci_exec.provider.Provider.{key}".format(key=key))

        return super().get_items(all_providers)

    def get_table(self, items):
        """Return parent class ``get_table`` with modified ``item``s."""
        desired_items = []
        for name, signature, summary_string, real_name in items:
            # This is going in the class docstring, so just use the basename.  E.g.,
            # ci_exec.utils.Provider.is_ci => is_ci
            name = name.split(".")[-1]
            desired_items.append((name, signature, summary_string, real_name))
        return super().get_table(desired_items)


def setup(app):  # noqa: D103
    app.add_css_file("custom.css")
    app.add_directive("dlistsummary", DefinitionListSummary)
    app.add_directive("availableproviders", ProviderSummary)

    app.add_node(Youtube, html=(visit_youtube_node, depart_youtube_node))
    app.add_directive("youtube", YoutubeDirective)
