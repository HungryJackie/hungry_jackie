from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from .models import Profile
from .forms import ProfileSetupForm


@login_required
@require_http_methods(["GET", "POST"])
def setup_profile(request):
    """첫 로그인 시 프로필 설정"""
    
    # 이미 프로필이 완성된 사용자는 홈으로 리다이렉트
    if hasattr(request.user, 'profile') and request.user.profile.is_profile_complete:
        return redirect('/')
    
    # Profile 객체가 없는 경우 생성 (signals가 작동하지 않은 경우 대비)
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                f'환영합니다, {profile.display_name}님! 프로필 설정이 완료되었습니다.'
            )
            return redirect('/')
    else:
        form = ProfileSetupForm(instance=profile)
    
    context = {
        'form': form,
        'user_email': request.user.email,
        'is_first_login': True
    }
    
    return render(request, 'profiles/setup_profile.html', context)


@login_required
def profile_view(request):
    """사용자 프로필 조회"""
    profile = get_object_or_404(Profile, user=request.user)
    
    context = {
        'profile': profile,
    }
    
    return render(request, 'profiles/profile_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"]) 
def edit_profile(request):
    """프로필 편집 (설정 완료 후)"""
    profile = get_object_or_404(Profile, user=request.user)
    
    if request.method == 'POST':
        form = ProfileSetupForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, '프로필이 성공적으로 업데이트되었습니다.')
            return redirect('profiles:profile')
    else:
        form = ProfileSetupForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile,
        'is_edit_mode': True
    }
    
    return render(request, 'profiles/setup_profile.html', context)