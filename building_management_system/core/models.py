from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Person(models.Model):
    person_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=255)
    nid = models.CharField(max_length=50, blank=True, default='')
    email = models.EmailField(blank=True, default='')
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    #profile_pic_url = models.URLField(blank=True, null=True)
    # profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # def set_password(self, raw_password):
    #     self.password = make_password(raw_password)

    # def check_password(self, raw_password):
    #     return check_password(raw_password, self.password)

    def __str__(self):
        return self.name

    # class Meta:
        # db_table = 'person'


class Resident(models.Model):
    RESIDENT_TYPES = [
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
    ]
    person = models.OneToOneField(Person, on_delete=models.CASCADE, primary_key=True, related_name='resident')
    resident_type = models.CharField(max_length=10, choices=RESIDENT_TYPES, default='tenant')

    def __str__(self):
        return self.person.name

    # class Meta:
    #     db_table = 'resident'


class Manager(models.Model):
    person = models.OneToOneField(Person, on_delete=models.CASCADE, primary_key=True, related_name='manager')

    def __str__(self):
        return self.person.name

    # class Meta:
         # db_table = 'manager'


class Building(models.Model):
    building_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.TextField()
    total_apartment = models.IntegerField(default=0)
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True, related_name='buildings')

    def __str__(self):
        return self.name

    # class Meta:
    #     db_table = 'building'


class Apartment(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='apartments')
    apartment_no = models.IntegerField()
    apartment_name = models.CharField(max_length=255, blank=True, default='')
    resident = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True, related_name='apartments')

    # class Meta:
    #     unique_together = ('building', 'apartment_no')
    #     db_table = 'apartment'

    def __str__(self):
        return f"{self.building.name} - Apt {self.apartment_no}"


class Billing(models.Model):
    BILL_TYPES = [
        ('rent', 'Rent'),
        ('service_charge', 'Service Charge'),
        ('water_bill', 'Water Bill'),
        ('gas_bill', 'Gas Bill'),
        ('electricity_bill', 'Electricity Bill'),
    ]
    bill_id = models.AutoField(primary_key=True)
    bill_type = models.CharField(max_length=20, choices=BILL_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_created = models.DateField(auto_now_add=True)
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, related_name='billings')
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, related_name='created_bills')
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='billings')

    def __str__(self):
        return f"Bill #{self.bill_id} - {self.get_bill_type_display()}"

    # class Meta:
    #     db_table = 'billing'


class PendingBill(models.Model):
    bill = models.OneToOneField(Billing, on_delete=models.CASCADE, primary_key=True, related_name='pending')
    due_date = models.DateField()

    def __str__(self):
        return f"Pending: {self.bill}"

    # class Meta:
    #     db_table = 'pending_bill'


class PaidBill(models.Model):
    bill = models.OneToOneField(Billing, on_delete=models.CASCADE, primary_key=True, related_name='paid')
    date_paid = models.DateField()

    def __str__(self):
        return f"Paid: {self.bill}"

    # class Meta:
    #     db_table = 'paid_bill'


class Complaint(models.Model):
    complaint_id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=100)
    description = models.TextField()
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='complaints')

    def __str__(self):
        return f"Complaint #{self.complaint_id} - {self.type}"

    # class Meta:
    #     db_table = 'complaint'


class PendingComplaint(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, primary_key=True, related_name='pending')
    date_posted = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Pending: {self.complaint}"

    # class Meta:
    #     db_table = 'pending_complaint'


class SolvedComplaint(models.Model):
    complaint = models.OneToOneField(Complaint, on_delete=models.CASCADE, primary_key=True, related_name='solved')
    date_solved = models.DateField()
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, related_name='solved_complaints')

    def __str__(self):
        return f"Solved: {self.complaint}"

    # class Meta:
    #     db_table = 'solved_complaint'


class Notice(models.Model):
    notice_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, null=True, blank=True, related_name='notices')
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, related_name='notices')

    def __str__(self):
        return self.title

    # class Meta:
    #     db_table = 'notice'