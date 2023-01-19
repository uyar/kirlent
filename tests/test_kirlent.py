from importlib import metadata

import kirlent


def test_installed_version_should_match_tested_version():
    assert metadata.version("kirlent") == kirlent.__version__
