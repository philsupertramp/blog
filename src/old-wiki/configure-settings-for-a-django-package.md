---
tags:
 - old-wiki
 - published
title: Configure settings for a django package
description: Create a system to configure your django package.
layout: mylayout.njk
author: Philipp
date: 2021-07-17
---

### Motivation
Over the years my side projects grew and recently I started working on [`django-data-migration`](https://github.com/philsupertramp/django-data-migration), a tool to simplify djangos migration graph by replacing pure data manipulating migrations into a dedicated graph.  
This tool essentially allows a developer to reduce the migration graph of an django application to its bare minimum.  
Not only the amount of side projects grew, but also my projects grew in complexity, this being said I started my journey to discover django's settings module.  
During my research I've been reading doc pages over doc pages and nothing gave me a clear overview of how to add settings to a package, therefor I decided to share the knowledge and discoveries I did while implementing them.


### Intro
Django comes with a huge feature, centralized settings within a single file called `settings.py`. This file is located per default in the projects configuration directory, but the user needs to provide the environment variable `DJANGO_SETTINGS_MODULE` pointing to your settings file (for example `DJANGO_SETTINGS_MODULE=mysite.settings`).
But what do you do if you don't have access over `DJANGO_SETTINGS_MODULE`, or more precise whenever you want to publish a configurable package which is used by others.
Something like
```python
DATA_MIGRATION = {
    "SQUASHABLE_APPS": ["mysite"]
}
```
### Limitations
It is required for an application to bootstrap django using
```python
import os  # optional
import django

# either configure manually
django.configure()
# or provide settings module
os.environ.set('DJANGO_SETTINGS_MODULE', 'myapp.settings')

django.setup()
```
For testing purposes we also get a nifty signal to hook into `setting_changed` which comes in handy whenever you do stuff like `override_settings` in your test suite.
But this also limits providing a settings module to the user of your application. **You can't** magically use two setting files. So somehow we need to figure out a way, how we can
maintain our internal configuration for the package, as well as allow the user of your package to provide customization.

### Idea
I came up with a simple three step plan, how I will tackle this problem. I will need to

- define structure how to store settings in package-project
- hook into the bootrapping workflow to get user settings
- keep settings up to date at any time


#### Data structure
Since my package is quite simple in regards of user configuration I provided the full needed set of settings above.  
But this is just for default settings, we also need some data structure we can easily access from all around the code base and keep up to date easly.

I decided to define a class which holds the user settings. The class is instatiated once, therefore we're building a simple [singleton](https://en.wikipedia.org/wiki/Singleton_pattern).
So I ended up with this `settings.py` for my package
```python
from typing import Dict, Optional


# default value definition
DATA_MIGRATION_DEFAULTS = {
    "SQUASHABLE_APPS": []
}


class DataMigrationSettings(object):
    """Broad implementation of a singleton. Internal class to hold and maintain package settings"""

    def __init__(self, user_settings=None, defaults: Optional[Dict] = None) -> None:
        """Constructor, allows passing no parameter, detects user provided settings and will use predefined default settings"""

        if defaults is None:
            defaults = DATA_MIGRATION_DEFAULTS

        self.settings = defaults.copy()
        if user_settings:
            self.update(user_settings)

    def update(self, settings) -> None:
        """Method to update setting values"""

        try:
            self.settings.update(getattr(settings, 'DATA_MIGRATION'))
        except AttributeError:
            self.settings.update(settings.get('DATA_MIGRATION', {}))

    def reload(self, settings) -> None:
        """Method to reload setting values from user settings"""
        try:
            _user_settings = getattr(settings, 'DATA_MIGRATION')
            self.settings = _user_settings
        except AttributeError:
            pass

    def __getattr__(self, item):
        """regular getter for setting values"""
        return self.settings[item]


# use this object in your code, do not recreate DataMigrationSettings or you will end up having inconsistent data
internal_settings = DataMigrationSettings(None)
```

The code above is quite self-explainatory, we have one single object in memory, provide initial data and allow updating the whole object or partially values as well as provide a method to reload user values from django's settings.

Now that we have the structure in place we also need to hook into djangos bootstrapping process. I discovered using the `AppConfig.ready` method is the perfect place to initially load the settings, since this method is called while bootstrapping the application, but prior to it the settings are already populated, so exactly what we need!
With that knowledge I added a simple call to `reload()` in my package's root directory's `apps.py`

```python
from django.conf import settings
from django.apps import AppConfig

from data_migration.settings import internal_settings


class DataMigrationsConfig(AppConfig):
    name = 'data_migration'
    verbose_name = 'Django data migrations'

    def ready(self):
        internal_settings.update(settings)
```
Finishing up with allowing to patch/change settings during runtime, we also need to hook into django's [`setting_changed`](https://docs.djangoproject.com/en/dev/ref/signals/#django.test.signals.setting_changed) signal.

So in `settings.py` of my package we add
```python
from django.core.signals import setting_changed

# previous code here...

def reload(sender, setting, value, *args, **kwargs):
    if setting == 'DATA_MIGRATION':
        internal_settings.update(value)


setting_changed.connect(reload)
```
Now we can rely on django's mechanics and workflows to do the right thing at the right time.  
**Also don't forget to provide your users some kind of API docs for your settings so they can easily configure the app without figuring out the keys for each setting!**


Hope this small intro/description helps you tackle your problem!
