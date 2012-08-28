from models import SimpleReservation
from forms import TemplatedForm
from django.contrib import admin
# Default reservation model
reservationModel = SimpleReservation


class DefaultReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'date')
    # list_filter = ('date',)
    date_hierarchy = 'date'


def get_form():
    """Returns templated model form for model that is currently set as reservationModel"""
    class ReservationForm(TemplatedForm):
        class Meta:
            model = reservationModel
            # exclude fields from standard Reservation model (show only extra ones in form)
            exclude = ('user', 'date', 'created', 'updated', )
    return ReservationForm


def update_model(newModel, newAdmin=None):
    """Update reservationModel variable and update Django admin to include it"""
    global reservationModel
    reservationModel = newModel
    from django.contrib import admin
    if not reservationModel in admin.site._registry:
        admin.site.register(reservationModel, DefaultReservationAdmin if not newAdmin else newAdmin)
