#!/usr/bin/env python
"""For use on CI machines, actually run the test rather than pseudo-tests."""

import argparse
import sys
from pathlib import Path

this_file_dir = Path(__file__).resolve().parent
repo_root = this_file_dir.parent
sys.path.insert(0, str(repo_root))

from tests.provider import Provider, provider_sum  # noqa: E402

if __name__ == "__main__":
    providers = [
        # Transform e.g., is_azure_pipelines to azure_pipelines (remove `is_`).
        "_".join(fn.__name__.split("_")[1:])
        for fn in Provider._all_provider_functions]

    providers.sort()
    parser = argparse.ArgumentParser("Provider Check")
    parser.add_argument("provider", choices=providers)

    args = parser.parse_args()

    assert Provider.is_ci()
    assert provider_sum() == 1
    for fn in Provider._all_provider_functions:
        if fn.__name__ == f"is_{args.provider}":
            assert fn()
        else:
            assert not fn()

    print(f"Unless you cheated, we're correctly detecting {args.provider}! :)")
