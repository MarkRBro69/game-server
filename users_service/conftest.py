import os
import pytest
import django


os.environ['DJANGO_SETTINGS_MODULE'] = 'users_service.settings'

django.setup()


@pytest.fixture(scope='session')
def django_db_setup():
    pass
