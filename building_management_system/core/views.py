from django.shortcuts import render, redirect
from django.db import connection
from .models import *
from django.contrib.auth.hashers import check_password
from django.utils.timezone import now
from django.contrib import messages
from django.conf import settings

def login_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        phone = request.POST.get('phone_number')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT person_id, name, password FROM core_person WHERE phone_number = %s",
                [phone]
            )
            row = cursor.fetchone()

        if not row:
            return render(request, 'login.html', {'error': 'Phone number not found.'})

        person_id, name, stored_password = row

        #if stored_password != password: ei kaj ta e hash diye kortesi for extra security
        if not check_password(password, stored_password):
            return render(request, 'login.html', {'error': 'Incorrect password.'})

        if role == 'resident':
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT person_id FROM core_resident WHERE person_id = %s",
                    [person_id]
                )
                if not cursor.fetchone():
                    return render(request, 'login.html', {'error': 'This person is not a resident.'})
            request.session['person_id'] = person_id #ekhane person id store hochhe
            request.session['role'] = 'resident'
            return redirect('resident_dashboard')

        elif role == 'manager':
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT person_id FROM core_manager WHERE person_id = %s",
                    [person_id]
                )
                if not cursor.fetchone():
                    return render(request, 'login.html', {'error': 'This person is not a manager.'})
            request.session['person_id'] = person_id #ekhane person id store hochhe
            request.session['role'] = 'manager'
            return redirect('manager_profile')

        else:
            return render(request, 'login.html', {'error': 'Please select a role.'})

    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()  # clears session completely
    return redirect('login')


def get_resident_sidebar(person_id):  #shob tab e jeno same jinish repeat hoi
    with connection.cursor() as cursor:

        # Person info
        cursor.execute("""
            SELECT name, profile_pic
            FROM core_person
            WHERE person_id = %s
        """, [person_id])

        person = cursor.fetchone()

        if person:
            name, profile_pic = person
        else:
            name, profile_pic = "Unknown", None

        if profile_pic:
            profile_pic = settings.MEDIA_URL + profile_pic

        # Resident type
        cursor.execute("""
            SELECT resident_type
            FROM core_resident
            WHERE person_id = %s
        """, [person_id])

        row = cursor.fetchone()
        resident_type = row[0] if row else "N/A"

        # Building + Apartment
        cursor.execute("""
            SELECT b.name, a.apartment_name
            FROM core_apartment a
            JOIN core_building b ON a.building_id = b.building_id
            WHERE a.resident_id = %s
            LIMIT 1
        """, [person_id])

        row = cursor.fetchone()

        if row:
            building_name, apartment_name = row
        else:
            building_name, apartment_name = "N/A", "N/A"

    return {
        'name': name,
        'profile_pic': profile_pic,
        'resident_type': resident_type,
        'building_name': building_name,
        'apartment_name': apartment_name,
    }
    
#resident dashboard

def resident_dashboard(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'resident':
        return redirect('login')

    sidebar = get_resident_sidebar(person_id)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(b.amount), 0)
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.resident_id = %s
        """, [person_id])

        unpaid_bills, total_due = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*)
            FROM core_pendingcomplaint pc
            JOIN core_complaint c ON pc.complaint_id = c.complaint_id
            WHERE c.resident_id = %s
        """, [person_id])

        active_complaints = cursor.fetchone()[0]

        cursor.execute("""
            SELECT n.title
            FROM core_notice n
            JOIN core_apartment a ON a.building_id = n.building_id
            WHERE a.resident_id = %s
            ORDER BY n.date DESC, n.notice_id DESC
            LIMIT 1
        """, [person_id])

        row = cursor.fetchone()
        latest_notice = row[0] if row else "No notices"

    context = {
        **sidebar,
        'unpaid_bills': unpaid_bills,
        'total_due': total_due,
        'active_complaints': active_complaints,
        'latest_notice': latest_notice,
    }

    return render(request, 'resident_templates/resident_dashboard.html', context)

def profile_view(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'resident':
        return redirect('login')

    sidebar = get_resident_sidebar(person_id)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT phone_number, email, nid
            FROM core_person
            WHERE person_id = %s
        """, [person_id])

        phone, email, nid = cursor.fetchone()

    context = {
        **sidebar,
        'phone': phone,
        'email': email,
        'nid': nid,
    }

    return render(request, 'resident_templates/resident_profile.html', context)

def resident_notices(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'resident':
        return redirect('login')

    sidebar = get_resident_sidebar(person_id)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT DISTINCT n.title, n.description, n.date
            FROM core_notice n
            JOIN core_apartment a ON n.building_id = a.building_id
            WHERE a.resident_id = %s
            ORDER BY n.date DESC, n.notice_id DESC
        """, [person_id])

        notices = cursor.fetchall()

    context = {
        **sidebar,
        'notices': notices,
    }

    return render(request, 'resident_templates/resident_notices.html', context)

def resident_billings(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'resident':
        return redirect('login')

    sidebar = get_resident_sidebar(person_id)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(b.amount), 0)
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.resident_id = %s
        """, [person_id])
        pending_count, pending_total = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(b.amount), 0)
            FROM core_paidbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.resident_id = %s
        """, [person_id])
        paid_count, paid_total = cursor.fetchone()

        cursor.execute("""
            SELECT b.bill_id, b.bill_type, b.amount, pb.due_date
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.resident_id = %s
        """, [person_id])
        pending_bills = cursor.fetchall()

        cursor.execute("""
            SELECT b.bill_id, b.bill_type, b.amount, pb.date_paid
            FROM core_paidbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.resident_id = %s
        """, [person_id])
        paid_bills = cursor.fetchall()

    context = {
        **sidebar,
        'pending_count': pending_count,
        'pending_total': pending_total,
        'paid_count': paid_count,
        'paid_total': paid_total,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
    }

    return render(request, 'resident_templates/resident_billings.html', context)


def pay_bill(request, bill_id):
    person_id = request.session.get('person_id')

    if request.method == 'POST':
        with connection.cursor() as cursor:

            # Ownership check
            cursor.execute("""
                SELECT b.bill_id
                FROM core_billing b
                JOIN core_resident r ON b.resident_id = r.person_id
                WHERE b.bill_id = %s AND r.person_id = %s
            """, [bill_id, person_id])

            if not cursor.fetchone():
                messages.error(request, "Invalid bill.")
                return redirect('resident_billings')

            # Delete from pending
            cursor.execute("""
                DELETE FROM core_pendingbill
                WHERE bill_id = %s
            """, [bill_id])

            # Insert into paid
            cursor.execute("""
                INSERT INTO core_paidbill (bill_id, date_paid)
                VALUES (%s, %s)
            """, [bill_id, now().date()])

        messages.success(request, "Payment successful!")

    return redirect('resident_billings')

def resident_complaints(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'resident':
        return redirect('login')

    sidebar = get_resident_sidebar(person_id)

    with connection.cursor() as cursor:

        if request.method == 'POST':
            ctype = request.POST.get('type')
            description = request.POST.get('description')

            cursor.execute("""
                INSERT INTO core_complaint (type, description, resident_id)
                VALUES (%s, %s, %s)
            """, [ctype, description, person_id])

            cursor.execute("SELECT LAST_INSERT_ID()")
            cid = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO core_pendingcomplaint (complaint_id, date_posted)
                VALUES (%s, %s)
            """, [cid, now()])

            return redirect('resident_complaints')

        cursor.execute("""
            SELECT c.type, c.description
            FROM core_pendingcomplaint pc
            JOIN core_complaint c ON pc.complaint_id = c.complaint_id
            WHERE c.resident_id = %s
        """, [person_id])
        pending = cursor.fetchall()

        cursor.execute("""
            SELECT c.type, c.description, sc.date_solved
            FROM core_solvedcomplaint sc
            JOIN core_complaint c ON sc.complaint_id = c.complaint_id
            WHERE c.resident_id = %s
        """, [person_id])
        solved = cursor.fetchall()

    context = {
        **sidebar,
        'pending': pending,
        'solved': solved,
    }

    return render(request, 'resident_templates/resident_complaints.html', context)


def get_manager_sidebar(person_id):
    with connection.cursor() as cursor:

        # Person info
        cursor.execute("""
            SELECT name, profile_pic
            FROM core_person
            WHERE person_id = %s
        """, [person_id])

        person = cursor.fetchone()

        if person:
            name, profile_pic = person
        else:
            name, profile_pic = "You are not a manager", None

        if profile_pic:
            profile_pic = settings.MEDIA_URL + profile_pic

        # Buildings managed
        cursor.execute("""
            SELECT b.name
            FROM core_building b
            WHERE b.manager_id = %s
        """, [person_id])
        buildings = cursor.fetchall()
        building_names = [b[0] for b in buildings] if buildings else []
        total_buildings = len(building_names)

    return {
        'name': name,
        'profile_pic': profile_pic,
        'building_names': building_names,
        'total_buildings': total_buildings,
    }


def manager_dashboard(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'manager':
        return redirect('login')

    sidebar = get_manager_sidebar(person_id)

    with connection.cursor() as cursor:

        # Total buildings
        cursor.execute("""
            SELECT COUNT(*)
            FROM core_building
            WHERE manager_id = %s
        """, [person_id])
        total_buildings = cursor.fetchone()[0]

        # Total residents in specific manager's buildings
        #distinct bad
        cursor.execute("""
            SELECT COUNT(DISTINCT a.resident_id)
            FROM core_apartment a
            JOIN core_building b ON a.building_id = b.building_id
            WHERE b.manager_id = %s AND a.resident_id IS NOT NULL
        """, [person_id])
        total_residents = cursor.fetchone()[0]

        # Due bills er total
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(b.amount), 0)
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = %s
        """, [person_id])
        pending_bills, pending_amount = cursor.fetchone()

        # Kotoguli complaint pending ache
        cursor.execute("""
            SELECT COUNT(*)
            FROM core_pendingcomplaint pc
            JOIN core_complaint c ON pc.complaint_id = c.complaint_id
            JOIN core_apartment a ON c.resident_id = a.resident_id
            JOIN core_building b ON a.building_id = b.building_id
            WHERE b.manager_id = %s
        """, [person_id])
        pending_complaints = cursor.fetchone()[0]

        # Recent notice
        cursor.execute("""
            SELECT n.title
            FROM core_notice n
            WHERE n.manager_id = %s
            ORDER BY n.date DESC, n.notice_id DESC
            LIMIT 1
        """, [person_id])
        row = cursor.fetchone()
        latest_notice = row[0] if row else "No notices"

    context = {
        **sidebar,
        'total_buildings': total_buildings,
        'total_residents': total_residents,
        'pending_bills': pending_bills,
        'pending_amount': pending_amount,
        'pending_complaints': pending_complaints,
        'latest_notice': latest_notice,
    }

    return render(request, 'manager_templates/manager_dashboard.html', context)


def manager_profile(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'manager':
        return redirect('login')

    sidebar = get_manager_sidebar(person_id)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT phone_number, email, nid
            FROM core_person
            WHERE person_id = %s
        """, [person_id])

        phone, email, nid = cursor.fetchone()

        # Buildings managed with details
        cursor.execute("""
            SELECT b.name, b.address, b.total_apartment
            FROM core_building b
            WHERE b.manager_id = %s
        """, [person_id])
        buildings = cursor.fetchall()

    context = {
        **sidebar,
        'phone': phone,
        'email': email,
        'nid': nid,
        'buildings': buildings,
    }

    return render(request, 'manager_templates/manager_profile.html', context)


def manager_notices(request):
    person_id = request.session.get('person_id') #session diye save kori
    role = request.session.get('role') # kon manager kortese

    if not person_id or role != 'manager':
        return redirect('login')

    sidebar = get_manager_sidebar(person_id)

    with connection.cursor() as cursor:

        if request.method == 'POST':
            title = request.POST.get('title')
            description = request.POST.get('description')
            building_id = request.POST.get('building_id')
            #create kortese complaint

            cursor.execute("""
                INSERT INTO core_notice (title, description, date, building_id, manager_id)
                VALUES (%s, %s, %s, %s, %s)
            """, [title, description, now().date(), building_id, person_id])

            return redirect('manager_notices')

        # Kon building select hocchee
        cursor.execute("""
            SELECT building_id, name
            FROM core_building
            WHERE manager_id = %s
        """, [person_id])
        buildings = cursor.fetchall()

        # Notices posted by this manager
        cursor.execute("""
            SELECT n.title, n.description, n.date, b.name
            FROM core_notice n
            LEFT JOIN core_building b ON n.building_id = b.building_id
            WHERE n.manager_id = %s
            ORDER BY n.date DESC, n.notice_id DESC
        """, [person_id])
        notices = cursor.fetchall()

    context = {
        **sidebar,
        'buildings': buildings,
        'notices': notices,
    }

    return render(request, 'manager_templates/manager_notices.html', context)


def manager_billings(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'manager':
        return redirect('login')

    sidebar = get_manager_sidebar(person_id)

    with connection.cursor() as cursor:

        if request.method == 'POST':
            bill_type = request.POST.get('bill_type')
            amount = request.POST.get('amount')
            apartment_id = request.POST.get('apartment_id')
            due_date = request.POST.get('due_date')

            # Get resident_id for this apartment
            cursor.execute("""
                SELECT a.resident_id
                FROM core_apartment a
                JOIN core_building b ON a.building_id = b.building_id
                WHERE a.id = %s AND b.manager_id = %s
            """, [apartment_id, person_id])
            row = cursor.fetchone()

            if not row or not row[0]:
                messages.error(request, "No such resident.")
                return redirect('manager_billings')

            resident_id = row[0]

            cursor.execute("""
                INSERT INTO core_billing (bill_type, amount, date_created, apartment_id, manager_id, resident_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [bill_type, amount, now().date(), apartment_id, person_id, resident_id])

            cursor.execute("SELECT LAST_INSERT_ID()")
            bill_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO core_pendingbill (bill_id, due_date)
                VALUES (%s, %s)
            """, [bill_id, due_date])

            messages.success(request, "Bill created successfully!")
            return redirect('manager_billings')

        # Summary counts
        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(b.amount), 0)
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = %s
        """, [person_id])
        pending_count, pending_total = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*), COALESCE(SUM(b.amount), 0)
            FROM core_paidbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = %s
        """, [person_id])
        paid_count, paid_total = cursor.fetchone()

        # Pending bills list
        cursor.execute("""
            SELECT b.bill_id, b.bill_type, b.amount, pb.due_date, p.name
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            JOIN core_person p ON b.resident_id = p.person_id
            WHERE b.manager_id = %s
        """, [person_id])
        pending_bills = cursor.fetchall()

        # Paid bills list
        cursor.execute("""
            SELECT b.bill_id, b.bill_type, b.amount, pb.date_paid, p.name
            FROM core_paidbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            JOIN core_person p ON b.resident_id = p.person_id
            WHERE b.manager_id = %s
        """, [person_id])
        paid_bills = cursor.fetchall()

        # Apartments for dropdown (from managed buildings, with a resident)
        cursor.execute("""
            SELECT a.id, a.apartment_name, b.name
            FROM core_apartment a
            JOIN core_building b ON a.building_id = b.building_id
            WHERE b.manager_id = %s AND a.resident_id IS NOT NULL
        """, [person_id])
        apartments = cursor.fetchall()

    context = {
        **sidebar,
        'pending_count': pending_count,
        'pending_total': pending_total,
        'paid_count': paid_count,
        'paid_total': paid_total,
        'pending_bills': pending_bills,
        'paid_bills': paid_bills,
        'apartments': apartments,
    }

    return render(request, 'manager_templates/manager_billings.html', context)


def manager_complaints(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'manager':
        return redirect('login')

    sidebar = get_manager_sidebar(person_id)

    with connection.cursor() as cursor:

        # Pending complaints from residents in managed buildings
        cursor.execute("""
            SELECT DISTINCT c.complaint_id, c.type, c.description, pc.date_posted, p.name
            FROM core_pendingcomplaint pc
            JOIN core_complaint c ON pc.complaint_id = c.complaint_id
            JOIN core_person p ON c.resident_id = p.person_id
            JOIN core_apartment a ON c.resident_id = a.resident_id
            JOIN core_building b ON a.building_id = b.building_id
            WHERE b.manager_id = %s
        """, [person_id])
        pending = cursor.fetchall()

        # Solved complaints by this manager
        cursor.execute("""
            SELECT c.type, c.description, sc.date_solved, p.name
            FROM core_solvedcomplaint sc
            JOIN core_complaint c ON sc.complaint_id = c.complaint_id
            JOIN core_person p ON c.resident_id = p.person_id
            WHERE sc.manager_id = %s
        """, [person_id])
        solved = cursor.fetchall()

    context = {
        **sidebar,
        'pending': pending,
        'solved': solved,
    }

    return render(request, 'manager_templates/manager_complaints.html', context)


def solve_complaint(request, complaint_id):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'manager':
        return redirect('login')

    if request.method == 'POST':
        with connection.cursor() as cursor:

            # Verify complaint is pending and belongs to a resident in manager's buildings
            cursor.execute("""
                SELECT pc.complaint_id
                FROM core_pendingcomplaint pc
                JOIN core_complaint c ON pc.complaint_id = c.complaint_id
                JOIN core_apartment a ON c.resident_id = a.resident_id
                JOIN core_building b ON a.building_id = b.building_id
                WHERE pc.complaint_id = %s AND b.manager_id = %s
            """, [complaint_id, person_id])

            if not cursor.fetchone():
                messages.error(request, "Invalid complaint.")
                return redirect('manager_complaints')

            # Delete from pending
            cursor.execute("""
                DELETE FROM core_pendingcomplaint
                WHERE complaint_id = %s
            """, [complaint_id])

            # Insert into solved
            cursor.execute("""
                INSERT INTO core_solvedcomplaint (complaint_id, date_solved, manager_id)
                VALUES (%s, %s, %s)
            """, [complaint_id, now().date(), person_id])

        messages.success(request, "Complaint resolved!")

    return redirect('manager_complaints')


def manager_residents(request):
    person_id = request.session.get('person_id')
    role = request.session.get('role')

    if not person_id or role != 'manager':
        return redirect('login')

    sidebar = get_manager_sidebar(person_id)

    with connection.cursor() as cursor:

        cursor.execute("""
            SELECT p.name, p.phone_number, p.email, r.resident_type,
                   a.apartment_name, b.name
            FROM core_apartment a
            JOIN core_building b ON a.building_id = b.building_id
            JOIN core_resident r ON a.resident_id = r.person_id
            JOIN core_person p ON r.person_id = p.person_id
            WHERE b.manager_id = %s
            ORDER BY b.name, a.apartment_name
        """, [person_id])
        residents = cursor.fetchall()

    context = {
        **sidebar,
        'residents': residents,
    }

    return render(request, 'manager_templates/manager_residents.html', context)


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
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_bills,
                COALESCE(SUM(amount), 0) AS total_amount
            FROM core_billing
            WHERE manager_id = %s
        """, [manager_id])
        total_bills, total_amount = cursor.fetchone()

        #  Paid bills 
        cursor.execute("""
            SELECT 
                COUNT(pb.bill_id),
                COALESCE(SUM(b.amount), 0)
            FROM core_paidbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = %s
        """, [manager_id])
        paid_count, paid_amount = cursor.fetchone()

        #  Pending bills (JOIN)
        cursor.execute("""
            SELECT 
                COUNT(pb.bill_id),
                COALESCE(SUM(b.amount), 0)
            FROM core_pendingbill pb
            JOIN core_billing b ON pb.bill_id = b.bill_id
            WHERE b.manager_id = %s
        """, [manager_id])
        pending_count, pending_amount = cursor.fetchone()

        # Solved complaints
        cursor.execute("""
            SELECT COUNT(*)
            FROM core_solvedcomplaint
            WHERE manager_id = %s
        """, [manager_id])
        solved_complaints = cursor.fetchone()[0]

        # Pending complaints 
        cursor.execute("""
            SELECT COUNT(*)
            FROM core_pendingcomplaint pc
            JOIN core_complaint c ON pc.complaint_id = c.complaint_id
            JOIN core_apartment a ON c.resident_id = a.resident_id
            JOIN core_building b ON a.building_id = b.building_id
            WHERE b.manager_id = %s
        """, [manager_id])
        pending_complaints = cursor.fetchone()[0]

        #  Total residents under this manager 
        cursor.execute("""
            SELECT COUNT(*)
            FROM core_resident
            WHERE person_id IN (
                SELECT resident_id
                FROM core_apartment
                WHERE building_id IN (
                    SELECT building_id
                    FROM core_building
                    WHERE manager_id = %s
                )
            )
        """, [manager_id])
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
