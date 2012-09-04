django-reservations
===================

A simple and customizable Django module for handling reservations. 

![Sample app screenshot using django-reservations](https://raw.github.com/bernii/django-reservations/master/screen1.jpg)

Features
--------

 * Customizable reservations (you can provide your own reservation model)
 * Configurable (single/multiple reservations per day, default free spots, reservations per month)
 * Automatic customizable emails with reservation details
 * Custom Django Admin backend
 * Ajax calendar for reservation creation and handling
 * UI based on [Twitter Bootstrap](http://twitter.github.com/bootstrap/)
 * Using i18n to handle translations

Usage
-----

You can use django-reseravations as any other django module. You have to add it to your Python PATH. After this add 'reservations' to your INSTALLED_APPS in settings.py. Also you need to set RESERVATION_SPOTS_TOTAL setting so app knows what is the reservations number limit per day. Add it to your urls.py:

```python

urlpatterns = patterns('',
    # ...
    url(r'^reservations/', include('reservations.urls')),
    # ...
)

````

After these basic steps you are ready to go. Just run *manage.py syncdb* to create suitable database models. The reservation app will be available under the URL */reservations/calendar*. Visit it to see how it works and how it looks like ;)

Customization
------------

You can also set some other settings to customize it further:

RESERVATIONS_PER_MONTH (unlimited by default) - how many reservations can a single user create during one month
RESERVATIONS_PER_DAY (unlimited by default) - how many reservations can a single user create on one day (for example user should not be able to make more than one reservation per day)

If you would like to add some extra data for each reservation (gender, nationality, whatever..) you can inherit Reservation model and extend it with you custom fields. After that the model will automatically use you new model (and it will update the UI too!). All the Django validation will work too (via ajax!).

The simplest way is to create a new app inside your project (myreservations for example) and add it to your *INSTALLED_APPS*. In your new app create *models.py* in which you will inherit from Reservation model. After creating your custom model you need to call *update_model* so Resevations module knows about your new model. 

```python

from django.db import models
from reservations import update_model
from reservations.models import Reservation

RACE = (
        ('alien', 'Killing Machine'),
        ('android', 'Artificial Inteligence'),
        ('human', 'Ordinary Guy'),
    )

class DetailedReservation(Reservation):
    """Your extra data for the basic model"""
    shoe_number = models.IntegerField()
    race = models.CharField(max_length=32, choices=RACE)

    def short_desc(self):
        """Displayed on the reservation removal button"""
        return str(self.id) + "/" + str(self.race)

update_model(DetailedReservation)

```


Customizing emails that are sent when reservation is being made can be easily done by creating *email_new.html* template file. Data available in the template is described below. You can check email_new.html template in reservations module for reference.

```python

{'name': username_of_the_user_that_made_a_reservation,
'date': date_of_the_reservation,
'reservation_id': reservation_id,
'extra_data': form_with_extra_data,
'domain': APP_URL_setting}

```


Testing
-------

Project has full unit test coverage of the backend. After adding it to your Django project you can run tests from your shell.

    ./manage.py test reservations

![Continuous Integration status](https://secure.travis-ci.org/bernii/django-reservations.png)


TODOs
-----

 * Sample app using Django reservations
 * Implemenging user requested features

Got some questions or suggestions? [Mail me](mailto:bkobos+ghdr@extensa.pl) directly or use the [issue tracker](django-reservations/issues).