from django.shortcuts import render
from users.models import DoctorProfile



# Create your views here.
def home(request):
    # return HttpResponse("Welcome to the Users Home Page")
    return render(request, 'pages/index.html')

def about(request):
    return render(request, 'pages/about.html')

def services(request):
    return render(request, 'pages/services.html')

def contact(request):
    return render(request, 'pages/contact.html')




def doctors(request):
    doctors = DoctorProfile.objects.filter(
        user__is_active=True,
        is_approved=True,
        is_available=True
    )

    context = {
        'doctors': doctors
    }
    return render(request, 'pages/doctors.html', context)