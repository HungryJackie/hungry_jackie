from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages


class CustomAccountAdapter(DefaultAccountAdapter):
    """계정 관련 커스터마이징"""
    
    def get_login_redirect_url(self, request):
        """로그인 후 리다이렉트 URL 결정"""
        user = request.user
        
        # Profile 객체가 없는 경우 생성 (signals가 작동하지 않은 경우 대비)
        from .models import Profile
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)
        
        # 프로필이 완성되지 않은 사용자는 프로필 설정으로
        if not user.profile.is_profile_complete:
            return reverse('profiles:setup_profile')
        
        # 프로필이 완성된 사용자는 기본 홈으로
        return '/'
    
    def add_message(self, request, level, message_tag, message, **kwargs):
        """로그인 관련 메시지는 추가하지 않음"""
        # message가 문자열이 아닌 경우 처리
        if not isinstance(message, str):
            return
            
        # 로그인 관련 메시지 필터링
        if 'login' not in message.lower() and '로그인' not in message:
            super().add_message(request, level, message_tag, message, **kwargs)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """소셜 계정 관련 커스터마이징"""
    
    def get_login_redirect_url(self, request):
        """소셜 로그인 후 리다이렉트 URL 결정"""
        user = request.user
        
        # Profile 객체가 없는 경우 생성 (signals가 작동하지 않은 경우 대비)
        from .models import Profile
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)
        
        # 프로필이 완성되지 않은 사용자는 프로필 설정으로
        if not user.profile.is_profile_complete:
            return reverse('profiles:setup_profile')
        
        # 프로필이 완성된 사용자는 기본 홈으로  
        return '/'
    
    def save_user(self, request, sociallogin, form=None):
        """소셜 로그인으로 사용자 저장 시 추가 처리"""
        user = super().save_user(request, sociallogin, form)
        
        # Profile 모델의 signal이 자동으로 생성하지만, 
        # 혹시 모를 상황에 대비해서 확인 후 생성
        from .models import Profile
        if not hasattr(user, 'profile'):
            Profile.objects.create(user=user)
            
        return user
    
    def add_message(self, request, level, message_tag, message, **kwargs):
        """로그인 관련 메시지는 추가하지 않음"""
        # message가 문자열이 아닌 경우 처리
        if not isinstance(message, str):
            return
            
        # 로그인 관련 메시지 필터링 (영문/한글 모두)
        message_lower = message.lower()
        if ('login' not in message_lower and 'sign' not in message_lower and 
            '로그인' not in message and 'successfully' not in message_lower):
            super().add_message(request, level, message_tag, message, **kwargs)