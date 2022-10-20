import sys


if sys.version_info < (3, 8):
    import importlib_metadata as metadata
else:
    from importlib import metadata

import kirlent


def test_installed_version_should_match_tested_version():
    assert metadata.version("kirlent") == kirlent.__version__
