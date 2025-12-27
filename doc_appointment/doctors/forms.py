from django import forms
from django.contrib.auth.forms import UserCreationForm
from users.models import User, DoctorProfile

class DoctorRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=50, required=True)
    email = forms.EmailField(required=True)
    specialization = forms.ChoiceField(
        choices=DoctorProfile.SPECIALIZATION_CHOICES,
        required=True
    )
    profile_picture = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'password1', 'password2')




from django import forms
from users.models import MedicalHistory

class MedicalHistoryForm(forms.ModelForm):

    class Meta:
        model = MedicalHistory
        fields = [
            'has_surgery',
            'smoker',
            'alcohol_use',
            'allergies',
            'chronic_conditions',
            'pain_severity',
            'notes',
        ]

        widgets = {
            'has_surgery': forms.Select(attrs={'class': 'form-control'}),
            'smoker': forms.Select(attrs={'class': 'form-control'}),
            'alcohol_use': forms.Select(attrs={'class': 'form-control'}),
            'pain_severity': forms.Select(attrs={'class': 'form-control'}),

            'allergies': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g., Penicillin, Dust, None'
                }
            ),

            'chronic_conditions': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'e.g., Diabetes, Hypertension'
                }
            ),

            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Other important medical remarks'
                }
            ),
        }

        labels = {
            'has_surgery': 'History of Surgery',
            'smoker': 'Smoking History',
            'alcohol_use': 'Alcohol Consumption',
            'allergies': 'Known Allergies',
            'chronic_conditions': 'Chronic Conditions',
            'pain_severity': 'Pain Severity',
            'notes': 'Additional Notes',
        }


class DoctorReplyForm(forms.Form):
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Type your message here...'
        })
    )