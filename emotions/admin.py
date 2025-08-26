# emotions/admin.py
from django.contrib import admin
from .models import Emotion, Genre, EmotionGenreRecommendation, UserEmotionEntry, Work


@admin.register(Emotion)
class EmotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'emoji', 'sub_description', 'color_code', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    ordering = ['order', 'name']


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'description']
    list_filter = ['category']
    search_fields = ['name', 'description']


class EmotionGenreRecommendationInline(admin.TabularInline):
    model = EmotionGenreRecommendation
    extra = 1
    fields = ['genre', 'priority', 'match_percentage', 'reason']


@admin.register(EmotionGenreRecommendation)
class EmotionGenreRecommendationAdmin(admin.ModelAdmin):
    list_display = ['emotion', 'genre', 'priority', 'match_percentage']
    list_filter = ['emotion', 'genre', 'priority']
    search_fields = ['emotion__name', 'genre__name']
    ordering = ['emotion', 'priority']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('emotion', 'genre', 'priority', 'match_percentage')
        }),
        ('추천 상세', {
            'fields': ('reason',),
            'classes': ('wide',)
        })
    )


@admin.register(UserEmotionEntry)
class UserEmotionEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'emotion', 'date', 'intensity', 'get_selected_genres_count']
    list_filter = ['emotion', 'date', 'intensity']
    search_fields = ['user__username', 'user__email', 'emotion__name']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    filter_horizontal = ['selected_genres']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('user', 'emotion', 'date', 'intensity')
        }),
        ('선택 사항', {
            'fields': ('selected_genres', 'note'),
            'classes': ('wide',)
        })
    )
    
    def get_selected_genres_count(self, obj):
        return obj.selected_genres.count()
    get_selected_genres_count.short_description = '선택 장르 수'


@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ['title', 'genre', 'platform', 'rating', 'is_active']
    list_filter = ['genre', 'platform', 'is_active']
    search_fields = ['title', 'genre__name']
    list_editable = ['is_active']
    ordering = ['-rating', 'title']