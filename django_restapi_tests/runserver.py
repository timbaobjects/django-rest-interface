#!/usr/bin/env python
from datetime import datetime
from random import randint

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
)

ROOT_URLCONF = 'django_restapi_tests.urls'

TEST_DATA = [
        ["XML, JSON or YAML?", ["XML", "JSON", "YAML"]],
        ["Google, MS or Yahoo?", ["Google", "MS", "Yahoo"]],
        ["Cheese or cherry", ["Cheese.", "Cherry."]]
]

def runserver(addr='localhost', port='8000'):
    from django.conf import settings, global_settings
    
    settings.configure(default_settings=global_settings, 
       DEBUG = True,
       DATABASE_NAME=':memory:', 
       DATABASE_ENGINE='sqlite3',
       ROOT_URLCONF = ROOT_URLCONF,
       INSTALLED_APPS = INSTALLED_APPS
    )
    
    # Reload DB module
    from django import db
    reload(db)
    
    # Disable the "create a super user" question
    from django.dispatch import dispatcher
    from django.contrib.auth.management import create_superuser
    from django.contrib.auth import models as auth_app
    from django.db.models import signals
    dispatcher.disconnect(create_superuser, sender=auth_app, signal=signals.post_syncdb)
    
    # Install Models
    from django.core import management
    settings.INSTALLED_APPS += ('django_restapi_tests.polls',)
    management.syncdb()
    
    # Create test data
    from django.contrib.auth.create_superuser import createsuperuser
    from polls.models import Poll, Choice
    for (question, answers) in TEST_DATA:
        p = Poll(question=question, pub_date=datetime.now())
        p.save()
        for answer in answers:
            c = Choice(poll=p, choice=answer, votes=randint(5, 50))
            c.save()
    
    # Create test user for admin site
    from django.contrib.auth.models import User
    try:
        User.objects.get(username="rest")
    except User.DoesNotExist:
        createsuperuser(username="rest", email="none@none.none", password="rest")
    
    # Run test server
    management.runserver(addr, port, use_reloader=False)

if __name__ == "__main__":
    runserver()
