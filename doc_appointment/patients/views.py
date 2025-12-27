from django.shortcuts import render, redirect, get_object_or_404
from .forms import PatientRegistrationForm     
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import logout   
from users.models import DoctorProfile, TimeSlot, Appointment, PatientProfile, Feedback      
from django.contrib import messages 
from django.http import JsonResponse
from users.models import Specialization
import datetime
from datetime import date, datetime




#----------------------------------------------------------------------------------
#Patient Registration View, Login View, Dashboard View and Profile View
#----------------------------------------------------------------------------------


def patient_register(request):
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            print("USER SAVED:", user.username)
            return redirect('login')
        else:
            # THIS is what you are missing
            print("FORM ERRORS:")
            print(form.errors)
            print("NON FIELD ERRORS:")
            print(form.non_field_errors())
    else:
        form = PatientRegistrationForm()

    return render(request, 'patients/register.html', {'form': form})






@login_required
@login_required
def patient_dashboard(request):
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return redirect('patient_profile')

    upcoming_appointments = Appointment.objects.filter(
        patient=patient_profile,
        appointment_date__gte=date.today()
    ).order_by('appointment_date', 'appointment_time')

    context = {
        'patient': patient_profile,
        'upcoming_appointments': upcoming_appointments
    }

    return render(request, 'patients/patient_dashboard.html', context)



@login_required
def edit_patient_profile(request):
    if request.user.role != 'patient':
        return redirect('index')

    profile = PatientProfile.objects.get(user=request.user)

    if request.method == 'POST':
        dob_str = request.POST.get('date_of_birth')

        if dob_str:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            profile.date_of_birth = dob

            today = date.today()
            profile.age = today.year - dob.year - (
                (today.month, today.day) < (dob.month, dob.day)
            )

        profile.gender = request.POST.get('gender')
        profile.email = request.POST.get('email')
        # profile.medical_history = request.POST.get('medical_history')

        profile.save()
        return redirect('patient_profile')

    return render(request, 'patients/edit_profile.html', {
        'profile': profile,
        'genders': PatientProfile.GENDER_CHOICES
    })




@login_required
def patient_profile(request):
    if request.user.role != 'patient':
        return redirect('index')

    profile = get_object_or_404(PatientProfile, user=request.user)

    return render(request, 'patients/patient_profile.html', {
        'profile': profile
    })


def patient_logout(request):
    logout(request)
    return render(request, 'pages/index.html')

#----------------------------------------------------------------------------------
# Appointment Booking and Related AJAX Views(time slots, doctors by specialization) cancellation
#----------------------------------------------------------------------------------





@login_required
def book_appointments(request):
    patient_profile = PatientProfile.objects.filter(user=request.user).first()
    if not patient_profile:
        messages.warning(request, "Please complete your profile first.")
        return redirect('patient_profile')

    SPECIALIZATION_CHOICES = DoctorProfile.SPECIALIZATION_CHOICES
    specializations = [{'value': val, 'label': label} for val, label in SPECIALIZATION_CHOICES]

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')

        if not doctor_id or not appointment_date or not appointment_time:
            messages.error(request, "All fields are required.")
            return redirect('book_appointments')

        doctor = get_object_or_404(DoctorProfile, id=doctor_id)

        appointment_date_obj = datetime.datetime.strptime(
            appointment_date, "%Y-%m-%d"
        ).date()

        appointment_time_obj = datetime.datetime.strptime(
            appointment_time, "%H:%M"
        ).time()

        today = datetime.date.today()

        # -------- RULE 1: Prevent past dates --------
        if appointment_date_obj < today:
            messages.error(request, "You cannot book an appointment for a past date.")
            return redirect('book_appointments')

        # -------- RULE 2: One appointment per doctor per day per patient --------
        existing_patient_booking = Appointment.objects.filter(
            doctor=doctor,
            patient=patient_profile,
            appointment_date=appointment_date_obj,
            status__in=['pending', 'confirmed']
        ).exists()

        if existing_patient_booking:
            messages.error(
                request,
                "You already have an appointment with this doctor on the selected date."
            )
            return redirect('book_appointments')

        # -------- RULE 3: Prevent slot collision --------
        slot_taken = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date_obj,
            appointment_time=appointment_time_obj,
            status__in=['pending', 'confirmed']
        ).exists()

        if slot_taken:
            messages.error(
                request,
                "This time slot is already booked. Please choose another time."
            )
            return redirect('book_appointments')

        Appointment.objects.create(
            doctor=doctor,
            patient=patient_profile,
            appointment_date=appointment_date_obj,
            appointment_time=appointment_time_obj,
            status='pending'
        )

        messages.success(request, "Appointment booked successfully!")
        return redirect('view_appointments')

    context = {
        'patient': patient_profile,
        'specializations': specializations,
    }
    return render(request, 'patients/book_appointments.html', context)







# AJAX view to get available slots
@login_required
def get_available_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})

    doctor = get_object_or_404(DoctorProfile, id=doctor_id)

    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({'slots': []})

    # Map weekday
    weekday_map = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    day_code = weekday_map[date_obj.weekday()]

    # Get doctor's availability windows
    availability_qs = TimeSlot.objects.filter(
        doctor=doctor,
        day_of_week=day_code,
        is_active=True
    )

    if not availability_qs.exists():
        return JsonResponse({'slots': []})

    # Get already booked times
    booked_times = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=date_obj,
        status__in=['pending', 'confirmed']
    ).values_list('appointment_time', flat=True)

    booked_set = set(bt.strftime("%H:%M") for bt in booked_times)

    SLOT_DURATION = datetime.timedelta(minutes=30)
    available_slots = []

    for slot in availability_qs:
        start_dt = datetime.datetime.combine(date_obj, slot.start_time)
        end_dt = datetime.datetime.combine(date_obj, slot.end_time)

        while start_dt + SLOT_DURATION <= end_dt:
            time_str = start_dt.strftime("%H:%M")

            if time_str not in booked_set:
                available_slots.append(time_str)

            start_dt += SLOT_DURATION

    return JsonResponse({'slots': available_slots})



@login_required
def get_doctors_by_specialization(request):
    specialization_value = request.GET.get('specialization')
    if not specialization_value:
        return JsonResponse({'doctors': []})

    doctors = DoctorProfile.objects.filter(
        specialization=specialization_value,
        is_approved=True,
        is_available=True
    )

    doctors_list = [
        {'id': doc.id, 'name': f"{doc.user.first_name} ({doc.get_specialization_display()})"}
        for doc in doctors
    ]
    return JsonResponse({'doctors': doctors_list})





@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, patient__user=request.user)
    appointment.status = 'cancelled'
    appointment.save()
    messages.success(request, "Appointment cancelled successfully.")
    return redirect('view_appointments')


@login_required
def view_appointments(request):
    """
    View to display all appointments of the logged-in patient
    """
    try:
        patient_profile = request.user.patientprofile
    except:
        patient_profile = None

    if not patient_profile:
        # Redirect if patient profile is not created yet
        messages.warning(request, "Please complete your profile first.")
        return redirect('patient_profile')

    # Fetch all appointments for this patient
    appointments = Appointment.objects.filter(
        patient=patient_profile
    ).order_by('-appointment_date', '-appointment_time')  # latest first

    context = {
        'patient': patient_profile,
        'appointments': appointments
    }

    return render(request, 'patients/view_appointments.html', context)

















@login_required
def submit_feedback(request):
    patient = request.user.patientprofile
    doctors = DoctorProfile.objects.all()  # or filter relevant doctors

    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        message = request.POST.get('message')

        if not doctor_id or not message:
            messages.error(request, "All fields are required.")
            return redirect('submit_feedback')

        doctor = get_object_or_404(DoctorProfile, id=doctor_id)
        Feedback.objects.create(patient=patient, doctor=doctor, message=message)
        messages.success(request, "Your feedback has been submitted successfully!")
        return redirect('patient_dashboard')

    context = {
        'doctors': doctors
    }
    return render(request, 'patients/submit_feedback.html', context)



from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from users.models import MedicalHistory
from users.models import PatientProfile

@login_required
def patient_medical_history(request):
    patient = get_object_or_404(PatientProfile, user=request.user)
    history = MedicalHistory.objects.filter(patient=patient).first()

    return render(
        request,
        'patients/medical_history.html',
        {
            'history': history,
            'patient': patient,
        }
    )



from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.conf import settings
import os
from users.models import PatientProfile, MedicalHistory

@login_required
def patient_medical_history_pdf(request):
    patient = get_object_or_404(PatientProfile, user=request.user)
    history = get_object_or_404(MedicalHistory, patient=patient)

    # Absolute path for logo (required for xhtml2pdf)
    logo_path = os.path.join(settings.STATIC_ROOT, 'img', 'pg_logo.png')

    html = render_to_string(
        'patients/medical_history_pdf.html',
        {
            'patient': patient,
            'history': history,
            'doctor': history.last_updated_by,
            'logo_path': logo_path,
        }
    )

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="medical_history.pdf"'

    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('Error generating PDF <pre>' + html + '</pre>')

    return response
