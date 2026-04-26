from django.shortcuts import render
from django.db import connection
from .models import *

def home_view(request):
    return render(request, 'home.html')

def persons_view(request):
    data = Person.objects.all()
    return render(request, 'persons.html', {'persons': data})

def residents_view(request):
    data = Resident.objects.all()
    return render(request, 'residents.html', {'residents': data})

def managers_view(request):
    data = Manager.objects.all()
    return render(request, 'managers.html', {'managers': data})

def buildings_view(request):
    data = Building.objects.all()
    return render(request, 'buildings.html', {'buildings': data})

def apartments_view(request):
    data = Apartment.objects.all()
    return render(request, 'apartments.html', {'apartments': data})

def billings_view(request):
    data = Billing.objects.all()
    return render(request, 'billings.html', {'bills': data})

def paid_bill_view(request):
    paid_bills = PaidBill.objects.all()
    
    return render(request, 'paid_bill.html', {
        'paid_bills': paid_bills
    })
    
def pending_bill_view(request):
    pending_bills = PendingBill.objects.all()
    
    return render(request, 'pending_bill.html', {
        'pending_bills': pending_bills
    })

def complaints_view(request):
    data = Complaint.objects.all()
    return render(request, 'complaints.html', {'complaints': data})

def PendingComplaint_view(request):
    data = PendingComplaint.objects.all()
    return render(request, 'PendingComplaint.html', {'pending_complaints': data})

def SolvedComplaint_view(request):
    data = SolvedComplaint.objects.all()
    return render(request, 'SolvedComplaint.html', {'solved_complaints': data})

def notices_view(request):
    data = Notice.objects.all()
    return render(request, 'notices.html', {'notices': data})

#temporary report
def manager_report_view(request, manager_id):

    with connection.cursor() as cursor:

        #  Total bills + total amount
        cursor.execute(f"""
            SELECT 
                COUNT(*) AS total_bills,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM core_billing
            WHERE manager_id = {manager_id}
        """)
        total_bills, total_amount = cursor.fetchone()

        #  Paid bills 
        cursor.execute(f"""
            SELECT 
                COUNT(pb.bill_id),
                COALESCE(SUM(b.amount), 0)
            FROM core_paidbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = {manager_id}
        """)
        paid_count, paid_amount = cursor.fetchone()

        #  Pending bills (JOIN)
        cursor.execute(f"""
            SELECT 
                COUNT(pb.bill_id),
                COALESCE(SUM(b.amount), 0)
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = {manager_id}
        """)
        pending_count, pending_amount = cursor.fetchone()

        # Solved complaints
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM core_solvedcomplaint
            WHERE manager_id = {manager_id}
        """)
        solved_complaints = cursor.fetchone()[0]

        # Pending complaints 
        cursor.execute("""
            SELECT COUNT(*)
            FROM core_pendingcomplaint
            WHERE complaint_id IN (
                SELECT complaint_id FROM core_complaint
            )
        """)
        pending_complaints = cursor.fetchone()[0]

        #  Total residents under this manager 
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM core_resident
            WHERE person_id IN (
                SELECT resident_id
                FROM core_apartment
                WHERE building_id IN (
                    SELECT building_id
                    FROM core_building
                    WHERE manager_id = {manager_id}
                )
            )
        """)
        total_residents = cursor.fetchone()[0]

    context = {
        'total_bills': total_bills,
        'total_amount': total_amount,
        'paid_count': paid_count,
        'paid_amount': paid_amount,
        'pending_count': pending_count,
        'pending_amount': pending_amount,
        'solved_complaints': solved_complaints,
        'pending_complaints': pending_complaints,
        'total_residents': total_residents,
    }

    return render(request, 'report.html', context)