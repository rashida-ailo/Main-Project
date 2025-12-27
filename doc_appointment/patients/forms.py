from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from users.models import PatientProfile

User = get_user_model()


class PatientRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=200)
    username = forms.CharField(max_length=50)

    # override password validation (allow short passwords)
    password1 = forms.CharField(
        widget=forms.PasswordInput,
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput,
        required=True
    )

    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    age = forms.IntegerField(required=False)
    gender = forms.ChoiceField(choices=PatientProfile.GENDER_CHOICES)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = (
            'first_name',
            'username',
            'password1',
            'password2',
            'date_of_birth',
            'age',
            'gender',
            'email',
        )

    def clean_password1(self):
        """
        Disable Django's default password validators
        (min length, complexity, etc.)
        """
        return self.cleaned_data.get("password1")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'patient'
        user.is_active = True
        user.email = self.cleaned_data.get('email')

        if commit:
            user.save()

            PatientProfile.objects.create(
                user=user,
                date_of_birth=self.cleaned_data['date_of_birth'],
                age=self.cleaned_data.get('age', 0),
                gender=self.cleaned_data['gender'],
                email=self.cleaned_data.get('email')
            )

        return user
