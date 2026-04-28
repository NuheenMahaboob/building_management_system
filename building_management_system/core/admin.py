from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import (
    Person, Resident, Manager, Building, Apartment,
    Billing, PendingBill, PaidBill,
    Complaint, PendingComplaint, SolvedComplaint,
    Notice
)


#----------------------------------------------person er modhee password deyar time e jeno hashed hoye save hoi
class PersonAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        # Hash password only if it's not already hashed
        if not obj.password.startswith('pbkdf2_'):
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)


admin.site.register(Person, PersonAdmin)  
#------------------------------------------------- person er modhee password deyar time e jeno hashed hoye save hoi


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