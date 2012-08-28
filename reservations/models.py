from django.db import models
from django.contrib.auth.models import User


class Reservation(models.Model):
    """Reservation model - who made a reservation and when"""
    user = models.ForeignKey(User)
    date = models.DateTimeField(null=False, blank=False)
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return str(self.date) + " User: " + str(self.user)

    def short_desc(self):
        """Default short description visible on reservation button"""
        return str(self.id)


class SimpleReservation(Reservation):
    """Default non-abstract fallback model used if user does not provide his own implementation"""
    pass


class ReservationDay(models.Model):
    """Reservation day model represeting single day and free/non-free spots for that day"""
    date = models.DateField(null=False, blank=False)
    spots_total = models.IntegerField(null=True, default=32)
    spots_free = models.IntegerField(null=True, default=32)

    def __unicode__(self):
        return str(self.date) + " Total: " + str(self.spots_total) + " Free: " + str(self.spots_free)


class Holiday(models.Model):
    """Define days that are free from work, you don't want to have reservations during holidays"""
    name = models.CharField(max_length=100, blank=True)
    date = models.DateField(null=False, blank=False)
    active = models.BooleanField(default=True, editable=True)
    # Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    def __unicode__(self):
        return str(self.name) + " " + str(self.date)
