from django.conf.urls.defaults import *
from django.views.generic.simple import *
from views import *
# Enable admin
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^month/(?P<month>\d*)/(?P<year>\d*)', MonthDetailView.as_view()),
    url(r'^reservation$', Reservation.as_view(), name='reservations_reservation'),
    url(r'^calendar$', calendar_view, name='reservations_calendar'),
    url(r'^holidays$', get_holidays, name='reservations_holidays'),
)
