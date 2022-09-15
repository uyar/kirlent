from pkg_resources import get_distribution

import kirlent


def test_installed_version_should_match_tested_version():
    assert get_distribution("kirlent").version == kirlent.__version__
