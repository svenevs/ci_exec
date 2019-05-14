Demos
========================================================================================

.. Hi there.  I've done something pretty sneaky here.  There are two parts to how it
.. works:
..
.. 1. Custom implementation of .. dlistsummary:: can be found in conf.py.  It makes it
..    so that instead of a table, you end up with a definition list that includes each
..    demo, the summary, and a link to the full demo.
..
.. 2. A :hidden: .. toctree::, which is the particularly sneaky part.  You need to have
..    the toctree there in order to not get warnings about "document not included in any
..    toctree" from Sphinx.  But this makes for an ugly layout (after the summary, you
..    just re-repeat everything?!).  But this makes it so that in the sidebar the link
..    actually goes to the full demo, not the injected heading.
..
.. It was kind of a happy accident, but it is quite nice :D

*More demos, particularly related to building C++, will be added when possible.*

.. currentmodule:: demos

.. dlistsummary::

    custom_log_stage

.. toctree::
   :maxdepth: 2
   :hidden:

   demos/custom_log_stage



Demos Program Execution
----------------------------------------------------------------------------------------

.. automodule:: demos.__main__
   :members:

    .. currentmodule:: demos.__main__

    .. autosummary::

        clear
        pause
        type_message
        mock_shell
        run_demo
