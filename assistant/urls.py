from django.urls import path

from .views import chat

urlpatterns = [path('asistente/consultar/', chat, name='assistant_chat')]
