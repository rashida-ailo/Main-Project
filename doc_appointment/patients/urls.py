from django.contrib import admin
from django.urls import path
from django.urls import path, include
from . import views
urlpatterns = [
    
    path('register/',views.patient_register,name="register"),
    path('',views.patient_dashboard,name="patient_dashboard"),

    path('book_appointment/',views.book_appointments,name="book_appointments"),
    path('view_appointments/',views.view_appointments,name="view_appointments"),
    path('cancel_appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    
    path('get-available-slots/', views.get_available_slots, name='get_available_slots'),
    path('get-doctors-by-specialization/', views.get_doctors_by_specialization, name='get_doctors_by_specialization'),

    
    path('patient_profile/',views.patient_profile,name="patient_profile"),
    path('edit_patient_profile/',views.edit_patient_profile,name="edit_patient_profile"),
    # path('patient_history/',views.patient_history,name="patient_history"),

    path('medical-history/',views.patient_medical_history,name='patient_medical_history'),
    path('medical-history/pdf/',views.patient_medical_history_pdf,name='patient_medical_history_pdf'),

    
    path('submit_feedback/',views.submit_feedback,name="submit_feedback"),
    path('logout/',views.patient_logout,name="patient_logout"),

]
