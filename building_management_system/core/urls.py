from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.home_view, name='home'),
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
    path('reports/', lambda request: views.manager_report_view(request, 1), name='reports')]