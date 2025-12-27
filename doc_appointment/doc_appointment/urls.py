"""
URL configuration for doc_appointment project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
   
    # Default Django admin (optional, for backend only)
    path('admin/', admin.site.urls),

    # Public pages
    path('', include('public_pages.urls')),  # Home, About, Contact

    # User / Account related
    path('accounts/', include('users.urls')),  # login, register, admin dashboard

    # Doctors app
    path('doctors/', include('doctors.urls')),

    # Patients app
    path('patients/', include('patients.urls')),

   
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
