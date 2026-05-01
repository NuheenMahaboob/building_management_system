from django.urls import path
from . import views
from functools import partial

urlpatterns = [
    # Common
    path('', views.login_view, name='login_root'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),

    # Admin/general views
    path('persons/', views.persons_view, name='persons'),
    path('residents/', views.residents_view, name='residents'),
    path('managers/', views.managers_view, name='managers'),
    path('buildings/', views.buildings_view, name='buildings'),
    path('apartments/', views.apartments_view, name='apartments'),
    path('billings/', views.billings_view, name='billings'),
    path('pending_bill/', views.pending_bill_view, name='pending_bill'),
    path('paid_bill/', views.paid_bill_view, name='paid_bill'),
    path('complaints/', views.complaints_view, name='complaints'),
    path('pending_complaints/', views.PendingComplaint_view, name='pending_complaints'),
    path('solved_complaints/', views.SolvedComplaint_view, name='solved_complaints'),
    path('notices/', views.notices_view, name='notices'),
    path('reports/', partial(views.manager_report_view, manager_id=1), name='reports'),


    # Resident views
    path('resident-dashboard/', views.resident_dashboard, name='resident_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('resident_notices/', views.resident_notices, name='resident_notices'),
    path('resident_billings/', views.resident_billings, name='resident_billings'),
    path('pay/<int:bill_id>/', views.pay_bill, name='pay_bill'),
    path('resident_complaints/', views.resident_complaints, name='resident_complaints'),
    # Manager views
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager-profile/', views.manager_profile, name='manager_profile'),
    path('manager-notices/', views.manager_notices, name='manager_notices'),
    path('manager-billings/', views.manager_billings, name='manager_billings'),
    path('manager-complaints/', views.manager_complaints, name='manager_complaints'),
    path('solve-complaint/<int:complaint_id>/', views.solve_complaint, name='solve_complaint'),
    path('manager-residents/', views.manager_residents, name='manager_residents'),
    path('manager-report/', views.manager_monthly_report, name='manager_report'),

]
