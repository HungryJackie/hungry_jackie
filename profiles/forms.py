from django import forms
from .models import Profile
import re


class ProfileSetupForm(forms.ModelForm):
    """첫 로그인 시 프로필 설정 폼"""
    
    class Meta:
        model = Profile
        fields = ['nickname', 'profile_image']
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '사용하실 닉네임을 입력해주세요',
                'maxlength': 20,
                'required': True
            }),
            'profile_image': forms.RadioSelect(attrs={
                'class': 'profile-image-radio'
            })
        }
        labels = {
            'nickname': '닉네임',
            'profile_image': '프로필 이미지 선택'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nickname'].required = True
        
        # 프로필 이미지 선택지는 기본 설정 그대로 사용 (텍스트 없이)
        # 템플릿에서 이미지만 표시하도록 처리
    
    def clean_nickname(self):
        """닉네임 유효성 검사"""
        nickname = self.cleaned_data.get('nickname')
        
        if not nickname:
            raise forms.ValidationError('닉네임을 입력해주세요.')
        
        # 길이 검사
        if len(nickname) < 2:
            raise forms.ValidationError('닉네임은 최소 2자 이상이어야 합니다.')
        
        if len(nickname) > 20:
            raise forms.ValidationError('닉네임은 20자를 초과할 수 없습니다.')
        
        # 특수문자 제한 (한글, 영문, 숫자, 일부 특수문자만 허용)
        if not re.match(r'^[가-힣a-zA-Z0-9_-]+$', nickname):
            raise forms.ValidationError('닉네임은 한글, 영문, 숫자, -, _만 사용할 수 있습니다.')
        
        # 중복 검사 (현재 사용자 제외)
        existing_profile = Profile.objects.filter(nickname=nickname)
        if self.instance and self.instance.pk:
            existing_profile = existing_profile.exclude(pk=self.instance.pk)
        
        if existing_profile.exists():
            raise forms.ValidationError('이미 사용중인 닉네임입니다. 다른 닉네임을 선택해주세요.')
        
        return nickname
    
    def save(self, commit=True):
        """프로필 저장 시 완료 상태로 변경"""
        profile = super().save(commit=False)
        profile.is_profile_complete = True
        if commit:
            profile.save()
        return profile