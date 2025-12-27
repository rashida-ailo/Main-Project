from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# -------------------------------------------------
# Specialization
# -------------------------------------------------
class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# -------------------------------------------------
# Doctor Profile
# -------------------------------------------------
# users/models.py
class DoctorProfile(models.Model):
    SPECIALIZATION_CHOICES = (
        ('general', 'General'),
        ('pediatrician', 'Pediatrician'),
        ('ob_gyn', 'Obstetrics and Gynaecology'),
        ('orthopedician', 'Orthopedician'),
        ('ent', 'ENT'),
        ('ophthalmologist', 'Ophthalmologist'),
        ('dentist', 'Dentist'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'doctor'}
    )
    specialization = models.CharField(
        max_length=50,
        choices=SPECIALIZATION_CHOICES,
        default='general'
    )
    qualification = models.CharField(max_length=150, blank=True)  # can be filled later
    experience_years = models.PositiveIntegerField(default=0, blank=True)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to='doctor_pics/',
        null=True,
        blank=True,
        default='doctor_pics/default.jpg'
    )
    is_available = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)  # Pending by default
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name or self.user.username


# -------------------------------------------------
# Patient Profile
# -------------------------------------------------

class PatientProfile(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'patient'}
    )
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    email = models.EmailField(max_length=150, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


# -------------------------------------------------
# Time Slot (Doctor Availability)
# -------------------------------------------------
class TimeSlot(models.Model):
    DAY_CHOICES = (
        ('mon', 'Monday'),
        ('tue', 'Tuesday'),
        ('wed', 'Wednesday'),
        ('thu', 'Thursday'),
        ('fri', 'Friday'),
        ('sat', 'Saturday'),
        ('sun', 'Sunday'),
    )

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    day_of_week = models.CharField(
        max_length=3,
        choices=DAY_CHOICES
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.doctor} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"


# -------------------------------------------------
# Appointment
# -------------------------------------------------
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    )

    CANCELLED_BY_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('admin', 'Admin'),
    )

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reason = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    cancelled_by = models.CharField(
        max_length=10,
        choices=CANCELLED_BY_CHOICES,
        blank=True,
        null=True
    )
    cancellation_reason = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient} → {self.doctor} on {self.appointment_date}"


#For doctor message to the admin

class DoctorMessage(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='messages',
        null=True,
        blank=True
    )

    # Whoever sends the message (doctor or admin)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_doctor_messages'
    )

    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sender_name = self.sender.get_username() if self.sender else "Doctor"
        return f"{sender_name} → {self.doctor.user.get_full_name()} | {self.subject}"
    



class Feedback(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)  # <- Add this field

    def __str__(self):
        return f"{self.patient.user.get_full_name} -> {self.doctor.user.get_full_name}"



class GeneralMedicalQuestion(models.Model):
    """
    A set of predefined medical questions that the doctor can select.
    Example: 'Does the patient smoke?', 'Any history of surgery?', etc.
    """
    question_text = models.CharField(max_length=255)

    def __str__(self):
        return self.question_text


class MedicalHistory(models.Model):
    YES_NO_CHOICES = (
        ('yes', 'Yes'),
        ('no', 'No'),
        ('unknown', 'Unknown'),
    )

    SEVERITY_CHOICES = (
        ('none', 'None'),
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
    )

    patient = models.OneToOneField(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='medical_history'
    )

    last_updated_by = models.ForeignKey(
        DoctorProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_medical_histories'
    )

    has_surgery = models.CharField(max_length=10, choices=YES_NO_CHOICES, default='unknown')
    smoker = models.CharField(max_length=10, choices=YES_NO_CHOICES, default='unknown')
    alcohol_use = models.CharField(max_length=10, choices=YES_NO_CHOICES, default='unknown')

    allergies = models.CharField(max_length=255, blank=True)
    chronic_conditions = models.TextField(blank=True)

    pain_severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='none')

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.patient and self.patient.user:
            return f"Medical history of {self.patient.user.get_full_name()}"
        return "Medical history (unassigned)"
