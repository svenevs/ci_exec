########################################################################################
# To the best of my knowledge, this is the appropriate license for this file.  Nobody  #
# seems to be maintaining sphinxcontrib-youtube, I decided to modify the version found #
# here https://github.com/sphinx-contrib/youtube which ultimately hails from the       #
# original BitBucket repo where this license text comes from:                          #
#                                                                                      #
#     https://bitbucket.org/birkenfeld/sphinx-contrib                                  #
#                                                                                      #
# There is an alternative that is sort-of packaged on PyPi as sphinxcontrib.youtube,   #
# but it doesn't work so I decided to just adapt the original for my needs.            #
########################################################################################
# If not otherwise noted, the extensions in this package are licensed                  #
# under the following license.                                                         #
#                                                                                      #
# Copyright (c) 2009 by the contributors (see AUTHORS file).                           #
# All rights reserved.                                                                 #
#                                                                                      #
# Redistribution and use in source and binary forms, with or without                   #
# modification, are permitted provided that the following conditions are               #
# met:                                                                                 #
#                                                                                      #
# * Redistributions of source code must retain the above copyright                     #
#   notice, this list of conditions and the following disclaimer.                      #
#                                                                                      #
# * Redistributions in binary form must reproduce the above copyright                  #
#   notice, this list of conditions and the following disclaimer in the                #
#   documentation and/or other materials provided with the distribution.               #
#                                                                                      #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS                  #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT                    #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR                #
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT                 #
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,                #
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT                     #
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,                #
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY                #
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT                  #
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE                #
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.                 #
########################################################################################
"""Enable the support of a ``.. youtube::`` directive."""

import textwrap

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import positive_int


class Youtube(nodes.General, nodes.Element):
    """The node class to add to Sphinx (see ``../conf.py:setup(app)``)."""

    pass


def visit_youtube_node(self, node):
    """Add the html for the specified node."""
    dest = node["dest"]
    width = node["width"]
    height = node["height"]

    # Generate the html text to add to the body.
    url = "https://www.youtube.com/embed/{dest}".format(dest=dest)
    backup = "https://youtu.be/{dest}".format(dest=dest)
    self.body.append(textwrap.dedent('''
        <div style="{div_style}">
          <iframe width="{width}" height="{height}" src="{url}" style="{iframe_style}" {defaults}>
            Your web browser does not appear to support iframe tags.  This video is
            located at <a href="{backup}">{backup}</a>
          </iframe>
        </div>
        <br />
    ''').format(  # noqa: E501
        div_style="; ".join([
            "position: relative",
            "height: 0",
            "padding-bottom: {aspect}%".format(
                aspect=(float(height) / float(width)) * 100.0
            ),
            "padding-top: 25px"
        ]),
        iframe_style="; ".join([
            "position: absolute",
            "top: 0",
            "left: 0",
            "width: 100%",
            "height: 100%"
        ]),
        width=width,
        height=height,
        url=url,
        defaults=(
            'frameborder="0" '
            'allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" '  # noqa: E501
            'allowfullscreen'
        ),
        backup=backup
    ))


def depart_youtube_node(self, node):
    """Do nothing, required by sphinx."""
    pass


class YoutubeDirective(Directive):
    """
    The directive class to add to Sphinx (see ``../conf.py:setup(app)``).

    Example usage:

    .. code-block:: rst

        .. youtube:: p4Gotl9vRGs

    By default it creates a 16:9 ratio video.  The ``:width:`` and ``:height:``
    attributes can be used to modify this behavior.  The defaults are ``width=560`` and
    ``height=315``, when you click on the "Share" link for YouTube, simply click on the
    "Embed" button and use the ``width`` and ``height`` shown in the sample ``<iframe>``
    tag.

    .. note::

        Percentage values are not supported, only positive integers.  The video aspect
        ratio is computed based off of the specified ``width`` and ``height``.  For
        example:

        .. code-block:: rst

            .. youtube:: p4Gotl9vRGs
               :width: 315
               :height: 560

        will produce a vertical video if you really wanted it.
    """

    has_content = False
    """This directive does not support any content."""

    required_arguments = 1
    """Exactly one argument is required: the video id."""

    option_spec = {
        "width": positive_int,
        "height": positive_int
    }
    """The options available: ``width`` and ``height``."""

    def run(self):
        """Return a :class:`Youtube` node with the specified url and dimensions."""
        dest = self.arguments[0]
        width = self.options.get("width", "560")
        height = self.options.get("height", "315")
        return [Youtube(dest=dest, width=width, height=height)]
