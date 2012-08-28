from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponseForbidden, HttpResponseBadRequest, HttpResponse
from django.template import RequestContext
from django.conf import settings
import time
import datetime
from django.db import models
from django.utils.simplejson import JSONEncoder
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.forms.models import model_to_dict
from models import *
from django.db.models import F
from django.utils.translation import ugettext as _
from . import get_form, reservationModel
from django import http
from django.utils import simplejson as json
from django.views.generic import View
import calendar
from utils import send_email


class DjangoJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, QuerySet):
            # `default` must return a python serializable
            # structure, the easiest way is to load the JSON
            # string produced by `serialize` and return it
            return serialize('python', obj)
        if isinstance(obj, models.Model):
            # do the same as above by making it a queryset first
            set_obj = [obj]
            set_str = serialize('python', set_obj)
            return set_str[0]
        if isinstance(obj, datetime.datetime):
            return time.mktime(obj.timetuple())
        if isinstance(obj, datetime.date):
            return time.mktime(obj.timetuple())
        return JSONEncoder.default(self, obj)


# From https://docs.djangoproject.com/en/1.4/topics/class-based-views/#more-than-just-html
class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context, cls=DjangoJSONEncoder)


class Reservation(JSONResponseMixin, View):
    @method_decorator(login_required)
    def post(self, request):
        year = int(request.POST['year'])
        month = int(request.POST['month'])
        day = int(request.POST['day'])
        date = datetime.date(year, month, day)

        # If user is using custom form, validate it
        form = get_form()(request.POST, initial={'user': request.user, 'date': date})
        if not form.is_valid():
            return self.render_to_response({'success': False,
                'errors': [(k, v[0]) for k, v in form.errors.items()]})

        # Check if it is not a holiday day
        if Holiday.objects.filter(date=datetime.date(year, month, day), active=True).count() != 0:
            return HttpResponseForbidden(_("You can not make reservations on holidays"))

        # Check if user can create new reservation in selected month
        # If reservations_per_month setting is set
        first, days_month = calendar.monthrange(year, month)
        if hasattr(settings, 'RESERVATIONS_PER_MONTH') and \
            reservationModel.objects.filter(user=request.user,
            date__gte=datetime.date(year, month, 1),
            date__lte=datetime.date(year, month, days_month)).count() >= settings.RESERVATIONS_PER_MONTH:
            return HttpResponseForbidden(_("You have already made a reservation during that month"))

        if hasattr(settings, 'RESERVATIONS_PER_DAY') and \
            reservationModel.objects.filter(user=request.user,
            date=datetime.date(year, month, day)).count() >= settings.RESERVATIONS_PER_DAY:
            return HttpResponseForbidden(_("You have already made a reservation during that day"))

        if not hasattr(settings, 'RESERVATION_SPOTS_TOTAL'):
            raise Exception("Critical error. Setting not set, contact admin")

        # Check if spot is still available
        reservation_day = ReservationDay.objects.get_or_create(date=date,
            defaults={'spots_free': settings.RESERVATION_SPOTS_TOTAL,
                      'spots_total': settings.RESERVATION_SPOTS_TOTAL})
        if reservation_day[0].spots_free < 1:
            return HttpResponseBadRequest(_("No spots free or reservation closed"))

        # Decrement counter on Reservation Day
        # SQL: UPDATE field_to_increment = field_to_increment + 1 ...
        reservation_day = reservation_day[0]
        reservation_day.spots_free = F('spots_free') - 1
        reservation_day.save()

        # Create reservation using current model
        reservation = form.save(commit=False)
        reservation.user = request.user
        reservation.date = date
        reservation.save()

        # Send email to user that the reservation has been sucessfully placed
        send_email(request.user.email, _('New booking | %s' % settings.APP_SHORTNAME), 'email_new.html',
            {'name': request.user.username,
             'date': date,
             'reservation_id': reservation.id,
             'extra_data': form,
             'domain': settings.APP_URL})

        reservation_dict = model_to_dict(reservation)
        reservation_dict['short_desc'] = reservation.short_desc()
        # Send fresh objects to user
        return self.render_to_response({"reservation": reservation_dict,
                                        "reservation_day": ReservationDay.objects.get(id=reservation_day.id),
                                        "error": None})

    @method_decorator(login_required)
    def delete(self, request):
        """Delete user reservation (if canceling reservation is still possible)"""
        reservation_id = int(request.REQUEST['id'])
        reservation = reservationModel.objects.get(id=reservation_id, user=request.user)
        if not reservation:
            return HttpResponseBadRequest(_("No such reservation"))
        timediff = datetime.datetime.combine(reservation.date, datetime.time()) - datetime.datetime.now()
        if timediff.days < 1:  # FUTURE TODO: Time resolution setting
            return HttpResponseForbidden(_("You have no access to modify this reservation, too late"))
        reservation.delete()
        # Suuccessfully deleted, increment spots_free for that day
        reservation_day = ReservationDay.objects.get(date=reservation.date)
        reservation_day.spots_free = F('spots_free') + 1
        reservation_day.save()

        return self.render_to_response({"reservation_day": ReservationDay.objects.get(id=reservation_day.id),
                                        "reservation": reservation,
                                        "id": reservation_id,
                                        "error": None})

    @method_decorator(login_required)
    def get(self, request):
        """Get all user reservations for particular year"""
        year = int(request.REQUEST['year'])
        reservations = reservationModel.objects.filter(
            date__gte=datetime.date(year, 1, 1),
            date__lte=datetime.date(year, 12, 31),
            user=request.user)
        # Convert reservations to dict for easier JSON seralization
        reservations_dict = []
        for reservation in reservations:
            elem = model_to_dict(reservation)
            elem['short_desc'] = reservation.short_desc()
            reservations_dict.append(elem)

        return self.render_to_response({"reservations": reservations_dict,
                                        "error": None})


def get_holidays(request):
    """Get holiday days in particular year"""
    year = int(request.REQUEST['year'])
    holidays = Holiday.objects.filter(
            date__gte=datetime.date(year, 1, 1),
            date__lte=datetime.date(year, 12, 31),
            active=True)
    return HttpResponse(json.dumps({"holidays": [model_to_dict(x) for x in holidays], "error": None}, cls=DjangoJSONEncoder), mimetype="application/json")


class MonthDetailView(JSONResponseMixin, View):
    """Get information about available spots for each day of particular month"""
    @method_decorator(login_required)
    def get(self, request, month, year):
        first, days_month = calendar.monthrange(int(year), int(month))
        date_from = datetime.date(int(year), int(month), 1)
        date_to = datetime.date(int(year), int(month), days_month)
        reservation_days = ReservationDay.objects.filter(
            date__gte=date_from,
            date__lte=date_to)
        return self.render_to_response(reservation_days)


@login_required
def calendar_view(request):
    """Calendar view available for logged in users"""
    from . import get_form, reservationModel
    form_details = get_form()
    defaults = {
        "spots_total": settings.RESERVATION_SPOTS_TOTAL,
        "get_extra_data": "true" if reservationModel != SimpleReservation else "false",
        "reservations_limit": getattr(settings, 'RESERVATIONS_PER_DAY', 0)
    }
    return render_to_response("calendar.html", dict(defaults=defaults, form_details=form_details),
        context_instance=RequestContext(request))
