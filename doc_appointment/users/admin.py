from django.contrib import admin
from django.utils.html import format_html

from .models import (
    User,
    Specialization,
    DoctorProfile,
    PatientProfile,
    TimeSlot,
    Appointment
)

# Register your models here.
@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'specialization']
    search_fields = ['user__username', 'user__first_name']
    actions = ['approve_doctors']

    def approve_doctors(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} doctor(s) approved successfully.")
    approve_doctors.short_description = "Approve selected doctors"


    
@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gender', 'date_of_birth')
    search_fields = ('user__username',)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'is_active')
    list_filter = ('day_of_week', 'is_active')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_date', 'status')
    list_filter = ('status',)