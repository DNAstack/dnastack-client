import importlib
import os

import pytest


@pytest.fixture(autouse=True)
def clean_metrics_env():
    os.environ.pop('DNASTACK_METRICS_ENABLED', None)
    yield
    os.environ.pop('DNASTACK_METRICS_ENABLED', None)


def test_metrics_enabled_defaults_to_false():
    import dnastack.feature_flags as ff
    importlib.reload(ff)
    assert ff.metrics_enabled is False


def test_metrics_enabled_is_true_when_set_to_1():
    os.environ['DNASTACK_METRICS_ENABLED'] = '1'
    import dnastack.feature_flags as ff
    importlib.reload(ff)
    assert ff.metrics_enabled is True
