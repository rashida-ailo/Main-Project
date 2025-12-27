from django.contrib import admin
from django.urls import path
from django.urls import path, include
from . import views
urlpatterns = [
    
    path('mydash/',views.doctor_today,name="doctor_dashboard"),
    
    

    path('doctor_appointments/',views.doctor_appointments,name="doctor_appointments"),

    path('medical_history/<int:patient_id>/', views.view_medical_history, name='view_medical_history'),
    path('doctors/add_medical_history/<int:patient_id>/<int:appointment_id>/', views.add_medical_history,name='add_medical_history'),

    path(
        'patient/<int:patient_id>/medical-history/edit/',
        views.add_or_edit_medical_history,
        name='add_medical_history'
    ),
    path(
    'doctor/appointment/<int:appointment_id>/history/',
    views.appointment_history,
    name='appointment_history'
    ),
    path('doctor_profile/',views.doctor_profile,name="doctor_profile"),
    path('doctor_availability/',views.doctor_availability,name="doctor_availability"),
    path('delete-time-slot/<int:slot_id>/', views.delete_time_slot, name='delete_time_slot'),
    path('availability/delete-multiple/',views.bulk_delete_time_slots,name='bulk_delete_time_slots'),
    
    path('messages/', views.doctor_messages, name='doctor_messages'),
    path('messages/reply/<int:message_id>/', views.doctor_reply_admin, name='doctor_reply_admin'),
    path('contact_admin/', views.contact_admin, name='contact_admin'),

    path('register/',views.doctor_register,name="doctor_register"),

    path('appointment/<int:appointment_id>/complete/', views.mark_appointment_completed, name='mark_appointment_completed'),

    path('edit_profile/',views.edit_doctor_profile,name="edit_doctor_profile"),

]
