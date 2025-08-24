"""
URL configuration for hungry_jackie project.

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
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # 커스텀 인증 뷰들 (allauth보다 먼저 정의해야 함)
    path('accounts/login/', views.login, name='account_login'),
    path('accounts/logout/', views.logout, name='account_logout'),

    path('accounts/', include('allauth.urls')),
    path('', views.home, name='home'),  # 메인 페이지를 위한 URL을 추가합니다.
]
