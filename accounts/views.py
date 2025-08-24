from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

def home(request):
    return render(request, 'home.html')

def login(request):
    """소셜 로그인만 지원하는 로그인 페이지"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'account/login.html')

@require_POST
@csrf_protect
def logout(request):
    """안전한 로그아웃 처리"""
    auth_logout(request)
    return redirect('/')