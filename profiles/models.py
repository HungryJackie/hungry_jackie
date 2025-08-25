from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """사용자 프로필 모델"""
    
    # 기본 프로필 이미지 선택지
    PROFILE_IMAGES = [
        ('default_1.png', '친근한 고양이'),
        ('default_2.png', '따뜻한 강아지'), 
        ('default_3.png', '차분한 올빼미'),
        ('default_4.png', '활발한 토끼'),
        ('default_5.png', '지혜로운 여우'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        verbose_name="사용자"
    )
    
    nickname = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="닉네임",
        help_text="2-20자 사이로 입력해주세요"
    )
    
    profile_image = models.CharField(
        max_length=40,
        choices=PROFILE_IMAGES,
        default='default_1.png',
        verbose_name="프로필 이미지"
    )
    
    is_profile_complete = models.BooleanField(
        default=False,
        verbose_name="프로필 설정 완료 여부"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="가입일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필들"
        
    def __str__(self):
        return f"{self.user.email}의 프로필"
    
    @property
    def display_name(self):
        """표시할 이름 반환 (닉네임이 있으면 닉네임, 없으면 이메일)"""
        return self.nickname if self.nickname else self.user.email.split('@')[0]
    
    def get_profile_image_url(self):
        """프로필 이미지 URL 반환"""
        return f"/static/images/profiles/{self.profile_image}"

    def get_profile_image_display(self):
        """프로필 이미지 표시명 반환"""
        for value, label in self.PROFILE_IMAGES:
            if value == self.profile_image:
                return label
        return "기본 이미지"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """User 생성 시 자동으로 Profile 생성"""
    if created:
        # 새 사용자 생성 시 프로필 생성
        Profile.objects.create(user=instance)
    else:
        # 기존 유저의 경우 Profile이 없으면 생성
        if not hasattr(instance, 'profile'):
            Profile.objects.create(user=instance)
        else:
            # 프로필이 있으면 저장 (updated_at 갱신)
            instance.profile.save()