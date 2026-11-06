"""
URL configuration for config project.

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
from core.views import home
from accounts.views import signup
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('cuentas/registro/', signup, name='signup'),
    path('cuentas/entrar/', auth_views.LoginView.as_view(), name='login'),
    path('cuentas/salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('vehiculos/', include('vehicles.urls')),
    path('', include('rentals.urls')),
    path('', include('assistant.urls')),
    path('admin/', admin.site.urls),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'DriveSmart · Administración'
admin.site.site_title = 'DriveSmart Admin'
admin.site.index_title = 'Gestión de DriveSmart'
