from django.urls import path

from . import views

urlpatterns = [
    path('vehiculos/<int:vehicle_id>/solicitar/', views.rental_create, name='rental_create'),
    path('mis-rentas/', views.rental_list, name='rental_list'),
    path('rentas/<int:pk>/confirmacion/', views.rental_confirmation, name='rental_confirmation'),
]
