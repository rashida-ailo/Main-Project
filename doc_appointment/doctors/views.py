from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from users.models import User, DoctorProfile, DoctorMessage, TimeSlot, MedicalHistory, PatientProfile
from .forms import DoctorRegistrationForm, MedicalHistoryForm
import datetime
from users.models import Appointment, TimeSlot
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Case, When, IntegerField




# View for doctor's dashboard showing today's appointments

@login_required
def doctor_today(request):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    today = datetime.date.today()

     # Today's appointments excluding cancelled
    appointments = Appointment.objects.filter(
        doctor=doctor_profile,
        appointment_date=today
    ).exclude(status='cancelled').order_by('appointment_time')

    # Count of unread messages from admin
    unread_messages_count = DoctorMessage.objects.filter(
        doctor=doctor_profile,
        sender__isnull=True,  # messages coming from admin
        is_read=False
    ).count()

    context = {
        'doctor': doctor_profile,
        'appointments': appointments,
        'unread_messages_count': unread_messages_count,
        'page': 'today'
    }
    return render(request, 'doctors/doctor_today.html', context)




@login_required
def doctor_appointments(request):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    today = datetime.date.today()

    appointments = Appointment.objects.filter(
        doctor=doctor_profile
    ).order_by('-appointment_date', '-appointment_time')

    # ---- Filters ----
    status = request.GET.get('status')
    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')

    if status:
        appointments = appointments.filter(status=status)

    if from_date:
        appointments = appointments.filter(appointment_date__gte=from_date)

    if to_date:
        appointments = appointments.filter(appointment_date__lte=to_date)

    context = {
        'doctor': doctor_profile,
        'appointments': appointments,
        'today': today,
        'page': 'all'
    }
    return render(request, 'doctors/doctor_appointments.html', context)


@login_required
def appointment_history(request, appointment_id):
    doctor = get_object_or_404(DoctorProfile, user=request.user)
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=doctor
    )

    history, created = MedicalHistory.objects.get_or_create(
        patient=appointment.patient
    )

    if request.method == 'POST':
        form = MedicalHistoryForm(request.POST, instance=history)
        if form.is_valid():
            form.save()

            # Optional: mark appointment completed
            appointment.status = 'completed'
            appointment.save()

            messages.success(request, "Medical history saved successfully.")
            return redirect('doctor_appointments')
    else:
        form = MedicalHistoryForm(instance=history)

    context = {
        'appointment': appointment,
        'form': form,
        'history': history
    }
    return render(request, 'doctors/appointment_history.html', context)





@login_required
def doctor_profile(request):
    # Allow only doctors
    if request.user.role != 'doctor':
        return redirect('index')

    # Get logged-in doctor's profile
    profile = get_object_or_404(DoctorProfile, user=request.user)

    context = {
        'profile': profile
    }

    return render(request, 'doctors/doctor_profile.html', context)




@login_required
def doctor_availability(request):
    # Get the doctor profile for the logged-in user
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)

    # Define the ordered days for display and table sorting
    days_of_week = TimeSlot.DAY_CHOICES
    weekday_order = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

    # Fetch time slots, ordered by weekdays and start_time
    time_slots = TimeSlot.objects.filter(doctor=doctor_profile).annotate(
        day_order=Case(
            *[When(day_of_week=day, then=idx) for idx, day in enumerate(weekday_order)],
            output_field=IntegerField()
        )
    ).order_by('day_order', 'start_time')

    # Handle form submission for adding new slots
    if request.method == 'POST':
        days = request.POST.getlist('days_of_week')  # Multiple days
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        if not days or not start_time or not end_time:
            messages.error(request, "All fields are required.")
            return redirect('doctor_availability')

        created_count = 0
        skipped_count = 0

        for day in days:
            # Check if this exact slot already exists
            exists = TimeSlot.objects.filter(
                doctor=doctor_profile,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time
            ).exists()

            if exists:
                skipped_count += 1
                continue

            # Create the time slot
            TimeSlot.objects.create(
                doctor=doctor_profile,
                day_of_week=day,
                start_time=start_time,
                end_time=end_time,
                is_active=True
            )
            created_count += 1

        # Feedback messages
        if created_count:
            messages.success(request, f"{created_count} time slot(s) added successfully.")
        if skipped_count:
            messages.warning(request, f"{skipped_count} slot(s) already existed and were skipped.")

        return redirect('doctor_availability')

    context = {
        'doctor': doctor_profile,
        'days_of_week': days_of_week,
        'time_slots': time_slots
    }

    return render(request, 'doctors/doctor_availability.html', context)


    




@login_required
def delete_time_slot(request, slot_id):
    slot = TimeSlot.objects.filter(id=slot_id, doctor__user=request.user).first()
    if slot:
        slot.delete()
        messages.success(request, "Time slot deleted successfully!")
    else:
        messages.error(request, "Time slot not found or you do not have permission.")
    return redirect('doctor_availability')


from users.models import DoctorProfile, DoctorMessage
from .forms import DoctorReplyForm

@login_required
def doctor_messages(request):
    # Get the doctor profile; if not found, redirect
    doctor_profile = DoctorProfile.objects.filter(user=request.user).first()
    if not doctor_profile:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_dashboard')

    # Inbox: messages sent by admin to this doctor
    inbox_messages = DoctorMessage.objects.filter(
        doctor=doctor_profile
    ).exclude(sender=request.user).order_by('-created_at')

    # Sent: messages sent by this doctor
    sent_messages = DoctorMessage.objects.filter(
        sender=request.user
    ).order_by('-created_at')

    context = {
        'inbox_messages': inbox_messages,
        'sent_messages': sent_messages,
    }
    return render(request, 'doctors/doctor_messages.html', context)



@login_required
def doctor_reply_admin(request, message_id):
    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    original_msg = get_object_or_404(DoctorMessage, id=message_id)

    if request.method == 'POST':
        form = DoctorReplyForm(request.POST)
        if form.is_valid():
            DoctorMessage.objects.create(
                doctor=None,  # admin is recipient
                sender=request.user,  # doctor sending
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                is_read=False
            )
            messages.success(request, "Reply sent to admin successfully!")
            return redirect('doctor_messages')
    else:
        form = DoctorReplyForm(initial={'subject': f"Re: {original_msg.subject}"})

    return render(request, 'doctors/doctor_reply.html', {
        'form': form,
        'original_msg': original_msg
    })


@login_required
def contact_admin(request):
    # Get the doctor profile of the logged-in user
    doctor_profile = DoctorProfile.objects.filter(user=request.user).first()
    if not doctor_profile:
        messages.error(request, "Doctor profile not found.")
        return redirect('doctor_dashboard')

    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if not subject or not message:
            messages.error(request, "Both subject and message are required.")
            return redirect('contact_admin')

        # Save message: doctor is sender, admin is recipient
        DoctorMessage.objects.create(
            doctor=doctor_profile,  # recipient is the doctor (to link for replies)
            sender=request.user,     # doctor is sender
            subject=subject,
            message=message,
            is_read=False
        )

        messages.success(request, "Message sent to admin successfully!")
        return redirect('doctor_messages')

    return render(request, 'doctors/contact_admin.html', {
        'doctor': doctor_profile
    })




def doctor_register(request):
    if request.method == 'POST':
        form = DoctorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            # Create user
            user = form.save(commit=False)
            user.role = 'doctor'
            user.is_active = True  # doctor can login only if approved
            user.save()

            # Create doctor profile with minimal info
            DoctorProfile.objects.create(
                user=user,
                specialization=form.cleaned_data['specialization'],
                profile_picture=form.cleaned_data.get('profile_picture'),
                is_approved=False
            )

            # Optionally show a success page
            return render(request, 'doctors/doctor_register_success.html', {'user': user})
        else:
            print(form.errors)  # debug invalid form
    else:
        form = DoctorRegistrationForm()

    return render(request, 'doctors/doctor_register.html', {'form': form})



def doctor_register_success(request):
    return render(request, 'doctors/doctor_register_success.html')



@login_required
def edit_doctor_profile(request):
    if request.user.role != 'doctor':
        return redirect('index')

    profile = DoctorProfile.objects.get(user=request.user)

    if request.method == 'POST':
        profile.specialization = request.POST.get('specialization')
        profile.qualification = request.POST.get('qualification')
        profile.experience_years = request.POST.get('experience_years') or 0
        profile.consultation_fee = request.POST.get('consultation_fee') or None
        profile.bio = request.POST.get('bio')

        if request.FILES.get('profile_picture'):
            profile.profile_picture = request.FILES.get('profile_picture')

        profile.save()
        return redirect('doctor_profile')

    return render(request, 'doctors/edit_profile.html', {
        'profile': profile,
        'specializations': DoctorProfile.SPECIALIZATION_CHOICES
    })



@login_required
def bulk_delete_time_slots(request):
    if request.method == 'POST':
        slot_ids = request.POST.getlist('slot_ids')

        TimeSlot.objects.filter(
            id__in=slot_ids,
            doctor__user=request.user
        ).delete()

        messages.success(request, "Selected time slots deleted successfully.")

    return redirect('doctor_availability')




@login_required
def mark_appointment_completed(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    appointment.status = 'completed'
    appointment.save()
    messages.success(request, f"Appointment with {appointment.patient.user.get_full_name()} marked as completed.")
    return redirect('doctor_today')


@login_required
def add_medical_history(request, patient_id, appointment_id=None):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    appointment = None
    if appointment_id:
        appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == "POST":
        form = MedicalHistoryForm(request.POST)
        if form.is_valid():
            medical_history = form.save(commit=False)
            medical_history.patient = patient
            medical_history.doctor = request.user.doctorprofile
            if appointment:
                medical_history.appointment = appointment
            medical_history.save()
            messages.success(request, "Medical history added successfully.")
            return redirect('doctor_dashboard')
    else:
        form = MedicalHistoryForm()

    context = {
        'form': form,
        'patient': patient,
        'appointment': appointment,
    }
    return render(request, 'doctors/add_medical_history.html', context)





@login_required
def view_medical_history(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)
    medical_history = get_object_or_404(MedicalHistory, patient=patient)

    return render(
        request,
        'doctors/view_medical_history.html',
        {
            'patient': patient,
            'history': medical_history
        }
    )



@login_required
def add_or_edit_medical_history(request, patient_id):
    patient = get_object_or_404(PatientProfile, id=patient_id)

    medical_history, created = MedicalHistory.objects.get_or_create(
        patient=patient
    )

    if request.method == "POST":
        form = MedicalHistoryForm(request.POST, instance=medical_history)
        if form.is_valid():
            history = form.save(commit=False)
            history.last_updated_by = request.user.doctorprofile
            history.save()
            messages.success(request, "Medical history updated successfully.")
            return redirect('view_medical_history', patient_id=patient.id)
    else:
        form = MedicalHistoryForm(instance=medical_history)

    return render(
        request,
        'doctors/add_medical_history.html',
        {
            'form': form,
            'patient': patient,
            'is_new': created
        }
    )
