#!/usr/bin/env python3
"""
Simple demo for how to modify the ``ci_exec`` defaults to suit user preferences.

Run this demo by cloning the repository:

.. code-block:: console

    $ git clone https://github.com/svenevs/ci_exec.git
    $ cd ci_exec
    $ python -m demos custom_log_stage

By default :func:`~ci_exec.colorize.log_stage` will log in bold green, using ``"="`` as
a separator.  This makes stages stick out / easy to spot during CI builds, but users may
not prefer this style.  Instead of manually calling with explicit arguments each time::

    from ci_exec import Colors, Styles, log_stage
    # ... some time later ...
    log_stage("CMake.Configure", color=Colors.Cyan, style=Styles.Regular, fill_char="-")

it is preferable to just create your own wrapper function.  If you want a ``"-"`` fill
character in regular cyan each time, why force yourself to type that out every time?  It
is much cleaner to just define your own wrapper with your preferred defaults.  The most
simple wrapper you can create::

    import ci_exec
    from ci_exec import Colors, Styles

    def log_stage(stage: str):
        ci_exec.log_stage(stage, color=Colors.Cyan, style=Styles.Regular, fill_char="-")

Chances are, this will satisfy 95% of use-cases.  The code in this file demonstrates how
you can enable keyword arguments on your wrapper function so that if you have a scenario
where you want to override your custom ``log_stage`` function defaults for just one or
two use cases you can.

You could of course just set ``ci_exec.log_stage.__kwdefaults__``, but changing this can
lead to some surprising behavior if you don't know what you are doing.  Additionally,
other readers will have a harder time following what your build script is doing.
"""

# These imports are only for the fake do_work function below.
import os
import shutil
import sys
import time

# NOTE: this path manipulation is to make it so we can run the script from the root of
# the repository (so we can `import ci_exec`).  You do not need to use this.
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import ci_exec  # noqa: E402
from ci_exec import Colors, Styles, colorize, merge_kwargs  # noqa: E402


def log_stage(stage: str, **kwargs):
    """Sample wrapper #1: provide custom behavior of log_stage."""
    # Use kwargs to still allow yourself to do bypasses on a single case.
    defaults = {
        "color": Colors.Cyan,
        "style": Styles.Bold,
        "fill_char": "-",
        "l_pad": "+== ",
        "r_pad": " ==+"
    }
    kwargs = merge_kwargs(defaults, kwargs)
    ci_exec.log_stage(stage, **kwargs)


def log_sub_stage(sub_stage: str, **kwargs):
    """Sample wrapper #2: enable sub-stages to be printed (e.g., for big scripts)."""
    # Similar approach, but using Styles.Regular and mostly spaces for a
    # supposed sub_stage :)
    defaults = {
        "color": Colors.Cyan,
        "style": Styles.Regular,
        "fill_char": ".",
        "l_pad": "::: ",
        "r_pad": " :::",
    }
    kwargs = merge_kwargs(defaults, kwargs)
    ci_exec.log_stage(sub_stage, **kwargs)


def bold_green(msg: str):
    """Sample wrapper #3: return ``msg`` in bold green text."""
    return colorize(msg, color=Colors.Green, style=Styles.Bold)


def do_work(n: int, width: int = shutil.get_terminal_size().columns):
    """Ignore this function, pretend this is the real work you need to do."""
    # Do "work" :D  (unimportant method, just filling space).
    work = "do some work. "
    num_work = width // len(work)
    all_work = work * num_work
    diff = width - len(all_work)
    if diff > 0:
        all_work += work[0:diff]

    if diff == 0:
        parts = [False for _ in range(num_work)]
    else:
        parts = all_work.split(work)

    # Give the illusion of do_work taking more time...
    for i in range(n):
        for p in parts:
            if not p:
                sys.stdout.write(work)
            else:
                sys.stdout.write(p)
            sys.stdout.flush()
            time.sleep(0.05)
        sys.stdout.write("\n")


def main():
    """Execute all build stages and log progress."""
    # Print using the default and then our custom log_stage to show difference.
    ci_exec.log_stage("Default Log")
    log_stage("Build Stage")

    # Execute first "sub stage"
    log_sub_stage("Sub Stage 1")
    do_work(1)

    # Execute second "sub stage"
    log_sub_stage("Sub Stage 2")
    do_work(2)

    # Execute third "sub stage".  Passing keyword arguments works as expected.
    log_sub_stage("Final Stage", l_pad="!!! ", r_pad=" !!!")
    do_work(3)

    # Let the reader know it's all gonna be ok.
    print(f"{bold_green('[+]')} All work completed successfully {bold_green(':)')}")


if __name__ == "__main__":
    main()
