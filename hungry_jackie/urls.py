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
from django.conf import settings
from django.conf.urls.static import static
from accounts import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # 커스텀 인증 뷰들 (allauth보다 먼저 정의해야 함)
    path('accounts/login/', views.login, name='account_login'),
    path('accounts/logout/', views.logout, name='account_logout'),

    # django-allauth URLs
    path('accounts/', include('allauth.urls')),
    
    # 프로필 관련 URLs
    path('profile/', include('profiles.urls')),

    # 감정 분석 시스템 URLs
    path('emotions/', include('emotions.urls')),
    
    # 메인 페이지
    path('', views.home, name='home'),
]


# 개발 환경에서 미디어 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)