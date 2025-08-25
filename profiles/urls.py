from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('setup/', views.setup_profile, name='setup_profile'),
    path('', views.profile_view, name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
]