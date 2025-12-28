from django.shortcuts import render,redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required,user_passes_test
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages 
from .decorator import admin_required
from users.models import DoctorProfile, DoctorMessage, PatientProfile,Appointment, Feedback



# Create your views here.


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # SUPERUSER FIRST
            if user.is_superuser:
                return redirect('admin_dashboard')

            # ROLE-BASED USERS
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'doctor':
                if not user.doctorprofile.is_approved:
                    messages.error(request, "Your account is pending admin approval.")
                    return redirect('login')
                else:
                    return redirect('doctor_dashboard')
            elif user.role == 'patient':
                return redirect('patient_dashboard')


        else:
            messages.error(request, "Invalid credentials")
            print("Invalid credentials")

    return render(request, 'accounts/login.html')







@login_required
@user_passes_test(admin_required)
def pending_doctors(request):
    pending = DoctorProfile.objects.filter(is_approved=False)

    if request.method == 'POST':
        action = request.POST.get('action')
        doctor_id = request.POST.get('doctor_id')
        doctor = DoctorProfile.objects.get(id=doctor_id)

        if action == 'approve':
            doctor.is_approved = True
            doctor.save()
        elif action == 'reject':
            doctor.user.delete()  # remove doctor account
        return redirect('pending_doctors')

    return render(request, 'accounts/pending_doctors.html', {'pending': pending})





@admin_required
@login_required
@user_passes_test(admin_required)
def admin_dashboard(request):
    total_doctors = DoctorProfile.objects.count()
    available_doctors = DoctorProfile.objects.filter(is_available=True).count()
    total_patients = PatientProfile.objects.count()
    total_appointments = Appointment.objects.count()
    unread_messages = DoctorMessage.objects.filter(is_read=False).count()
    doctors_list = DoctorProfile.objects.all()

    # Pending doctors
    pending_doctors_count = DoctorProfile.objects.filter(is_approved=False).count()

    context = {
        'total_doctors': total_doctors,
        'available_doctors': available_doctors,
        'total_patients': total_patients,
        'total_appointments': total_appointments,
        'unread_messages': unread_messages,
        'doctors_list': doctors_list,
        'pending_doctors_count': pending_doctors_count,
    }
    return render(request, 'accounts/admin_dashboard.html', context)





@login_required
def admin_edit_doctor(request, doctor_id):
    if request.user.role != 'admin':
        return redirect('index')

    doctor = DoctorProfile.objects.select_related('user').get(id=doctor_id)

    if request.method == 'POST':
        doctor.specialization = request.POST.get('specialization')
        doctor.qualification = request.POST.get('qualification')
        doctor.experience_years = request.POST.get('experience_years')
        doctor.consultation_fee = request.POST.get('consultation_fee')
        doctor.save()

        messages.success(request, "Doctor details updated successfully")
        return redirect('admin_manage_doctors')

    return render(request, 'accounts/edit_doctor.html', {
        'doctor': doctor,
        'specializations': DoctorProfile.SPECIALIZATION_CHOICES
    })


@login_required
def manage_patients(request):
    patients = PatientProfile.objects.select_related('user')
    return render(
        request,
        'accounts/manage_patients.html',
        {'patients': patients}
    )

@login_required
def patient_appointments(request, patient_id):
    patient = get_object_or_404(
        PatientProfile.objects.select_related('user'),
        id=patient_id
    )

    appointments = (
        Appointment.objects
        .filter(patient=patient)
        .select_related('doctor', 'doctor__user')
        .order_by('-appointment_date', '-appointment_time')
    )

    return render(
        request,
        'accounts/patient_appointments.html',
        {
            'patient': patient,
            'appointments': appointments
        }
    )



@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def admin_doctor_messages(request):
    # Only admins can access
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission to view this page.")
        return redirect('index')

    # Inbox: messages sent by doctors to admin
    inbox_messages = DoctorMessage.objects.filter(
        sender__isnull=False  # Must have a sender (doctor)
    ).order_by('-created_at')

    # Sent: messages sent by admin to doctors
    sent_messages = DoctorMessage.objects.filter(
        sender=request.user
    ).order_by('-created_at')

    context = {
        'inbox_messages': inbox_messages,
        'sent_messages': sent_messages,
    }
    return render(request, 'accounts/doctor_messages.html', context)


@login_required
def mark_message_read(request, message_id):
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission.")
        return redirect('index')

    msg = get_object_or_404(DoctorMessage, id=message_id)
    msg.is_read = True
    msg.save()

    return redirect('admin_doctor_messages')


def manage_doctors(request):
    doctors = DoctorProfile.objects.all()
    return render(request, 'accounts/manage_doctors.html', {'doctors': doctors})


def toggle_doctor_availability(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    doctor.is_available = not doctor.is_available
    doctor.save()
    return redirect('manage_doctors')





def patient_messages(request):
    """
    Admin view to display messages sent by patients.
    """
    messages_list = Feedback.objects.select_related('patient__user', 'doctor__user').order_by('-created_at')
    context = {
        'messages_list': messages_list
    }
    return render(request, 'accounts/patient_messages.html', context)



def mark_patient_message_read(request, message_id):
    """
    Mark a patient message as read
    """
    msg = get_object_or_404(Feedback, id=message_id)
    msg.is_read = True
    msg.save()
    messages.success(request, f"Message from {msg.patient.user.get_full_name} marked as read.")
    return redirect('patient_messages')




from users.models import DoctorMessage
from .forms import DoctorReplyForm, DoctorMessageForm

@login_required
def reply_doctor_message(request, message_id):
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission to send replies.")
        return redirect('index')

    # Get the original doctor message
    doctor_msg = get_object_or_404(DoctorMessage, id=message_id)

    if request.method == 'POST':
        form = DoctorReplyForm(request.POST)
        if form.is_valid():
            # Create a new message back to doctor
            DoctorMessage.objects.create(
                doctor=doctor_msg.doctor,          # recipient doctor
                sender=request.user,                # admin is sending
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                is_read=False                       # doctor hasn't read the reply yet
            )
            messages.success(request, "Reply sent successfully!")
            return redirect('admin_doctor_messages')
    else:
        # Prefill subject with "Re: original subject"
        form = DoctorReplyForm(initial={'subject': f"Re: {doctor_msg.subject}"})

    context = {
        'form': form,
        'doctor_msg': doctor_msg,
    }
    return render(request, 'accounts/reply_doctor_message.html', context)




@login_required
def compose_doctor_message(request):
    if request.user.role != 'admin':
        messages.error(request, "You do not have permission to send messages.")
        return redirect('index')

    if request.method == 'POST':
        form = DoctorMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user  # admin is sending
            msg.save()
            messages.success(request, "Message sent successfully!")
            return redirect('admin_doctor_messages')
    else:
        form = DoctorMessageForm()

    context = {
        'form': form
    }
    return render(request, 'accounts/compose_doctor_message.html', context)

