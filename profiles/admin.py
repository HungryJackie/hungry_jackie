from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile


class ProfileInline(admin.StackedInline):
    """User 관리 페이지에서 Profile을 함께 관리"""
    model = Profile
    can_delete = False
    verbose_name_plural = '프로필'
    fields = ('nickname', 'profile_image', 'is_profile_complete', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class UserAdmin(BaseUserAdmin):
    """사용자 관리자에 프로필 인라인 추가"""
    inlines = (ProfileInline,)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """프로필 관리자"""
    list_display = [
        'user_email', 
        'nickname', 
        'profile_image_display',
        'is_profile_complete', 
        'created_at'
    ]
    list_filter = ['is_profile_complete', 'profile_image', 'created_at']
    search_fields = ['user__email', 'nickname']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'nickname', 'profile_image')
        }),
        ('상태', {
            'fields': ('is_profile_complete',)
        }),
        ('날짜 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_email(self, obj):
        """사용자 이메일 표시"""
        return obj.user.email
    user_email.short_description = '이메일'
    user_email.admin_order_field = 'user__email'
    
    def profile_image_display(self, obj):
        """프로필 이미지 표시"""
        return obj.get_profile_image_display()
    profile_image_display.short_description = '프로필 이미지'


# 기존 User admin 등록 해제 후 새로운 것으로 등록
admin.site.unregister(User)
admin.site.register(User, UserAdmin)