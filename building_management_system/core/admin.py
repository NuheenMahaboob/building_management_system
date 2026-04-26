from django.contrib import admin
from .models import (
    Person, Resident, Manager, Building, Apartment,
    Billing, PendingBill, PaidBill,
    Complaint, PendingComplaint, SolvedComplaint,
    Notice
)

admin.site.register(Person)
admin.site.register(Resident)
admin.site.register(Manager)
admin.site.register(Building)
admin.site.register(Apartment)
admin.site.register(Billing)
admin.site.register(PendingBill)
admin.site.register(PaidBill)
admin.site.register(Complaint)
admin.site.register(PendingComplaint)
admin.site.register(SolvedComplaint)
admin.site.register(Notice)