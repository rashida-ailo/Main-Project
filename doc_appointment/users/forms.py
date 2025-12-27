from django import forms

class DoctorReplyForm(forms.Form):
    subject = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    message = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}))




from .models import DoctorMessage, DoctorProfile

class DoctorMessageForm(forms.ModelForm):
    class Meta:
        model = DoctorMessage
        fields = ['doctor', 'subject', 'message']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }