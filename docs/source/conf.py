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
from types import FunctionType

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
    "sphinx.ext.viewcode",
    "sphinx_issues"
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

# See: https://github.com/sloria/sphinx-issues
issues_github_path = "svenevs/ci_exec"


def get_all_top_level():
    """Return list of fully qualified strings for ci_exec top level names."""
    top_level = []
    for item in ci_exec.__all__:
        module = getattr(ci_exec, item).__module__
        full_item = "{module}.{item}".format(module=module, item=item)
        top_level.append(full_item)

    return top_level


def top_level_replacements():
    """Return list of rst replacement text."""
    top_level = get_all_top_level()
    all_repl = []
    for full in top_level:
        base = full.split(".")[-1]
        if isinstance(getattr(ci_exec, base), FunctionType):
            short = "{base}()".format(base=base)
        else:
            short = base
        repl = ".. |{base}| replace:: :any:`{short} <{full}>`".format(
            base=base, short=short, full=full
        )
        all_repl.append(repl)
    return all_repl


# Make top-level imports available directly using substitutions.
rst_epilog = "\n".join(top_level_replacements())


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


# NOTE: inherit ProviderSummary to re-use its get_table.
class CoreSummary(Autosummary):
    """Generate an autosummary for ci_exec top-level namespace."""

    def get_items(self, names):
        """Return parent class ``get_items`` with dynamic ``names`` list."""
        all_items = []
        for item in ci_exec.__all__:
            module = getattr(ci_exec, item).__module__
            full_item = "{module}.{item}".format(module=module, item=item)
            all_items.append(full_item)

        return super().get_items(all_items)

    def get_table(self, items):
        """Return parent class ``get_table`` with modified ``item``s."""
        desired_items = []
        for name, signature, summary_string, real_name in items:
            # This is going in the class docstring, so just use the basename.  E.g.,
            # ci_exec.utils.Provider.is_ci => is_ci
            name = name.split(".")[-1]
            desired_items.append((name, signature, summary_string, real_name))
        return super().get_table(desired_items)


def monkey_patch_autodoc():  # noqa D100
    # https://github.com/sphinx-doc/sphinx/issues/6361
    # Adding temporary monkey patch solution until we discuss how to properly fix.
    # This code is directly from
    # https://github.com/sphinx-doc/sphinx/blob/165897a74951fb03e497d6e05496ce02e897f820/sphinx/ext/autodoc/__init__.py#L406-L408
    def format_signature(self):  # noqa D100
        if self.args is not None:
            # signature given explicitly
            args = "(%s)" % self.args
        else:
            # try to introspect the signature
            try:
                args = self.format_args()
            except Exception as err:
                logger.warning(__('error while formatting arguments for %s: %s') %  # noqa
                                (self.fullname, err), type='autodoc')  # noqa
                args = None

        retann = self.retann

        ################################################################################
        # See: https://github.com/sphinx-doc/sphinx/issues/6361                        #
        result = self.env.events.emit_firstresult('autodoc-process-signature',         #
                                                  self.objtype, self.fullname,         #
                                                  self.object, self.options, args,     #
                                                  retann, self)                        #
        ################################################################################
        if result:
            args, retann = result

        if args is not None:
            return args + (retann and (' -> %s' % retann) or '')
        else:
            return ''

    from sphinx.ext.autodoc import Documenter
    Documenter.format_signature = format_signature


def autodoc_process_signature(app, what, name, obj, options, signature,
                              return_annotation, documenter):
    """
    Remove type hints from all signatures for improved readability.

    - See `autodoc-process-signature event`__
    - See https://github.com/sphinx-doc/sphinx/issues/6361

    __ http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#event-autodoc-process-signature
    """  # noqa E501
    try:
        return documenter.format_args(show_annotation=False), return_annotation
    except:  # noqa E722
        return None


def setup(app):  # noqa: D103
    monkey_patch_autodoc()

    app.add_css_file("custom.css")
    app.add_directive("dlistsummary", DefinitionListSummary)
    app.add_directive("availableproviders", ProviderSummary)
    app.add_directive("coresummary", CoreSummary)

    app.add_node(Youtube, html=(visit_youtube_node, depart_youtube_node))
    app.add_directive("youtube", YoutubeDirective)

    app.connect("autodoc-process-signature", autodoc_process_signature)
