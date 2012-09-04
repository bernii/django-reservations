#!/usr/bin/env python

import os, sys
from django.conf import settings

DIRNAME = os.path.dirname(__file__)
settings.configure(DEBUG=True,
                   DATABASES={
                        'default': {
                            'ENGINE': 'django.db.backends.sqlite3',
                        }
                    },
                   ROOT_URLCONF='reservations.urls',
                   INSTALLED_APPS=('django.contrib.auth',
                                  'django.contrib.contenttypes',
                                  'django.contrib.sessions',
                                  'django.contrib.admin',
                                  'reservations',),
                   # App specific settings
                   RESERVATION_SPOTS_TOTAL=32,
                   APP_SHORTNAME="test-reservations",
                   APP_URL="http://127.0.0.1:8000",
                   EMAIL_FROM="autbot@extensa.pl",),

from django.test.simple import DjangoTestSuiteRunner
test_runner = DjangoTestSuiteRunner(verbosity=1)
failures = test_runner.run_tests(['reservations', ])
if failures:
    sys.exit(failures)
