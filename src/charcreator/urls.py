from django.urls import path
from . import views

urlpatterns = [
    path('', views.character_list, name='character_list'),
]
