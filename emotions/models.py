# emotions/models.py
from django.db import models
from django.contrib.auth.models import User


class Emotion(models.Model):
    """감정 모델"""
    name = models.CharField(max_length=20, unique=True, verbose_name="감정명")
    emoji = models.CharField(max_length=10, verbose_name="이모지")
    color_code = models.CharField(max_length=7, default='#6366f1', verbose_name="색상코드")
    description = models.TextField(blank=True, verbose_name="설명")
    sub_description = models.CharField(max_length=50, blank=True, verbose_name="부제목")
    is_active = models.BooleanField(default=True, verbose_name="활성상태")
    order = models.IntegerField(default=0, verbose_name="정렬순서")
    
    class Meta:
        verbose_name = "감정"
        verbose_name_plural = "감정들"
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.emoji} {self.name}"


class Genre(models.Model):
    """장르 모델"""
    name = models.CharField(max_length=50, unique=True, verbose_name="장르명")
    description = models.TextField(verbose_name="설명")
    category = models.CharField(max_length=30, default='웹툰', verbose_name="카테고리")
    
    class Meta:
        verbose_name = "장르"
        verbose_name_plural = "장르들"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EmotionGenreRecommendation(models.Model):
    """감정-장르 추천 매핑"""
    emotion = models.ForeignKey(Emotion, on_delete=models.CASCADE, verbose_name="감정")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name="장르")
    priority = models.IntegerField(verbose_name="우선순위")  # 1, 2, 3 순위
    reason = models.TextField(verbose_name="추천 이유")
    match_percentage = models.IntegerField(default=80, verbose_name="매치율")
    
    class Meta:
        verbose_name = "감정-장르 추천"
        verbose_name_plural = "감정-장르 추천들"
        unique_together = ['emotion', 'genre']
        ordering = ['emotion', 'priority']
    
    def __str__(self):
        return f"{self.emotion.name} → {self.genre.name} ({self.priority}순위)"


class UserEmotionEntry(models.Model):
    """사용자 감정 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="사용자")
    emotion = models.ForeignKey(Emotion, on_delete=models.CASCADE, verbose_name="감정")
    date = models.DateField(verbose_name="날짜")
    selected_genres = models.ManyToManyField(Genre, blank=True, verbose_name="선택한 장르들")
    note = models.TextField(blank=True, verbose_name="메모")
    intensity = models.IntegerField(default=5, verbose_name="강도")  # 1-10
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일시")
    
    class Meta:
        verbose_name = "사용자 감정 기록"
        verbose_name_plural = "사용자 감정 기록들"
        unique_together = ['user', 'date']  # 하루에 하나의 감정만
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.emotion.name} ({self.date})"


# 향후 확장을 위한 작품 모델 (현재는 사용하지 않음)
class Work(models.Model):
    """작품 모델 (향후 확장용)"""
    title = models.CharField(max_length=100, verbose_name="작품명")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, verbose_name="장르")
    platform = models.CharField(max_length=50, verbose_name="플랫폼")
    url = models.URLField(blank=True, verbose_name="URL")
    rating = models.FloatField(null=True, blank=True, verbose_name="평점")
    thumbnail = models.URLField(blank=True, verbose_name="썸네일")
    is_active = models.BooleanField(default=True, verbose_name="활성상태")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "작품"
        verbose_name_plural = "작품들"
        ordering = ['-rating', 'title']
    
    def __str__(self):
        return self.title