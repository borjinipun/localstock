"""Shared pytest config: celery runs eagerly in tests (no redis needed)."""
import pytest

from config.celery import app as celery_app


@pytest.fixture(autouse=True)
def celery_eager():
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)
    yield
    celery_app.conf.update(task_always_eager=False, task_eager_propagates=False)
