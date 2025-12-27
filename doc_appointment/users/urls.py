from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('login/',views.user_login,name="login"),

    path('',views.admin_dashboard,name="admin_dashboard"),
    # path('manage_doctors/',views.manage_doctors,name="admin_manage_doctors"),
    path('admin_edit_doctor/<int:doctor_id>/',views.admin_edit_doctor,name="admin_edit_doctor"),
       
        
    path('pending-doctors/', views.pending_doctors, name='pending_doctors'),
    path('messages/', views.admin_doctor_messages, name='admin_doctor_messages'),

    path('manage_patients/',views.manage_patients,name="manage_patients"),
    path('patients/', views.manage_patients, name='admin_manage_patients'),
    path('patients/<int:patient_id>/appointments/',views.patient_appointments,name='admin_patient_appointments'),

    
    path('doctors/', views.manage_doctors, name='manage_doctors'),
    path('doctor/availability/<int:doctor_id>/',views.toggle_doctor_availability,name='toggle_doctor_availability'),
    path('doctor-messages/read/<int:message_id>/',views.mark_message_read,name='mark_message_read'),

    path('patient-messages/', views.patient_messages, name='patient_messages'),
    path('patient-messages/read/<int:message_id>/',views.mark_patient_message_read,name='mark_patient_message_read'),
    path('doctor-message/reply/<int:message_id>/', views.reply_doctor_message, name='reply_doctor_message'),
    path('doctor-messages/compose/', views.compose_doctor_message, name='compose_doctor_message'),

    path('logout/',views.user_logout,name="logout"),
]
