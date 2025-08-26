# 1. characters/models.py 수정 (결제 관련 부분 간소화)

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from emotions.models import Genre
import uuid
import os


def character_image_path(instance, filename):
    """캐릭터 이미지 업로드 경로 설정"""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4().hex}.{ext}'
    return f'character_images/{instance.creator.id}/{filename}'


class Character(models.Model):
    """AI 캐릭터 모델"""
    
    VISIBILITY_CHOICES = [
        ('public', '공개'),
        ('private', '비공개'),
    ]
    
    STATUS_CHOICES = [
        ('active', '활성'),
        ('pending', '검토 중'),
        ('suspended', '정지'),
    ]
    
    # 기본 정보
    name = models.CharField(max_length=50, verbose_name="캐릭터명")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="생성자")
    description = models.TextField(verbose_name="캐릭터 설명")
    
    # 캐릭터 설정
    personality = models.TextField(verbose_name="성격 설정")
    background_story = models.TextField(verbose_name="배경 이야기")
    speaking_style = models.TextField(verbose_name="말투/대화 스타일")
    
    # 장르 및 태그
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name="장르")
    tags = models.CharField(max_length=200, verbose_name="태그들", help_text="쉼표로 구분")
    
    # 이미지
    character_image = models.ImageField(
        upload_to=character_image_path, 
        blank=True, 
        null=True, 
        verbose_name="캐릭터 이미지"
    )
    
    # 설정
    visibility = models.CharField(
        max_length=10, 
        choices=VISIBILITY_CHOICES, 
        default='public',
        verbose_name="공개 설정"
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active',  # 개발 중에는 자동 승인
        verbose_name="상태"
    )
    
    # 통계
    total_conversations = models.IntegerField(default=0, verbose_name="총 대화 수")
    rating_sum = models.IntegerField(default=0, verbose_name="평점 합계")
    rating_count = models.IntegerField(default=0, verbose_name="평점 개수")
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "캐릭터"
        verbose_name_plural = "캐릭터들"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (by {self.creator.username})"
    
    @property
    def average_rating(self):
        """평균 평점 계산"""
        if self.rating_count == 0:
            return 0
        return round(self.rating_sum / self.rating_count, 1)
    
    def get_tags_list(self):
        """태그 리스트 반환"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]


class Conversation(models.Model):
    """대화 세션 모델"""
    
    STATUS_CHOICES = [
        ('active', '진행 중'),
        ('paused', '일시 정지'),
        ('ended', '종료'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    character = models.ForeignKey(Character, on_delete=models.CASCADE, verbose_name="캐릭터")
    title = models.CharField(max_length=100, verbose_name="대화 제목", blank=True)
    
    # 대화 설정
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='active',
        verbose_name="상태"
    )
    
    # 통계
    message_count = models.IntegerField(default=0, verbose_name="메시지 수")
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="시작일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="마지막 활동")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="종료일")
    
    class Meta:
        verbose_name = "대화"
        verbose_name_plural = "대화들"
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}님과 {self.character.name}의 대화"
    
    def auto_generate_title(self):
        """첫 메시지를 기반으로 제목 자동 생성"""
        if not self.title:
            first_message = self.messages.filter(sender='user').first()
            if first_message:
                content = first_message.content[:30]
                self.title = f"{content}..." if len(first_message.content) > 30 else content
                self.save()


class Message(models.Model):
    """대화 메시지 모델"""
    
    SENDER_CHOICES = [
        ('user', '사용자'),
        ('character', '캐릭터'),
        ('system', '시스템'),
    ]
    
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name="대화"
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES, verbose_name="발신자")
    content = models.TextField(verbose_name="메시지 내용")
    
    # AI 관련 메타데이터 (선택사항)
    ai_model_used = models.CharField(max_length=50, blank=True, verbose_name="사용된 AI 모델")
    generation_time = models.FloatField(null=True, blank=True, verbose_name="생성 시간(초)")
    
    # 시간 정보
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="전송 시간")
    
    class Meta:
        verbose_name = "메시지"
        verbose_name_plural = "메시지들"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.get_sender_display()}: {self.content[:50]}..."


# 개발용 간단한 크레딧 시스템 (결제 시스템 없이)
class UserCredit(models.Model):
    """사용자 크레딧 모델 (개발용 간소화 버전)"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="사용자")
    free_credits = models.IntegerField(default=50, verbose_name="무료 크레딧")  # 개발용으로 많이 지급
    
    # 시간 정보
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "사용자 크레딧"
        verbose_name_plural = "사용자 크레딧들"
    
    def __str__(self):
        return f"{self.user.username}의 크레딧"
    
    @property
    def total_credits(self):
        """총 보유 크레딧"""
        return self.free_credits
    
    def use_credits(self, amount):
        """크레딧 사용"""
        if self.free_credits >= amount:
            self.free_credits -= amount
            self.save()
            return True
        return False


class CharacterRating(models.Model):
    """캐릭터 평점 모델"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    character = models.ForeignKey(Character, on_delete=models.CASCADE, verbose_name="캐릭터")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="평점"
    )
    review = models.TextField(blank=True, verbose_name="리뷰")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")
    
    class Meta:
        verbose_name = "캐릭터 평점"
        verbose_name_plural = "캐릭터 평점들"
        unique_together = ['user', 'character']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.character.name}: {self.rating}점 ({self.user.username})"


# Signal을 통한 자동 생성
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_credit(sender, instance, created, **kwargs):
    """사용자 생성 시 크레딧 객체 자동 생성"""
    if created:
        UserCredit.objects.create(user=instance)

@receiver(post_save, sender=CharacterRating)
def update_character_rating(sender, instance, **kwargs):
    """평점 저장 시 캐릭터의 평균 평점 업데이트"""
    character = instance.character
    ratings = CharacterRating.objects.filter(character=character)
    
    character.rating_sum = sum(rating.rating for rating in ratings)
    character.rating_count = ratings.count()
    character.save()

@receiver(post_save, sender=Message)
def update_conversation_stats(sender, instance, created, **kwargs):
    """메시지 생성 시 대화 통계 업데이트"""
    if created:
        conversation = instance.conversation
        conversation.message_count += 1
        conversation.save()
        
        # 캐릭터 대화 수 업데이트
        if instance.sender == 'user':
            conversation.character.total_conversations += 1
            conversation.character.save()

