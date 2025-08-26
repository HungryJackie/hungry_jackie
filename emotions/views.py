# emotions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
import json

from .models import Emotion, Genre, EmotionGenreRecommendation, UserEmotionEntry


def emotion_selection(request):
    """감정 선택 페이지"""
    emotions = Emotion.objects.filter(is_active=True).order_by('order', 'name')
    
    context = {
        'emotions': emotions,
        'page_title': '오늘 기분이 어떠신가요?'
    }
    
    return render(request, 'emotions/emotion_selection.html', context)


@login_required
def get_recommendations(request, emotion_id):
    """선택된 감정에 대한 장르 추천"""
    emotion = get_object_or_404(Emotion, id=emotion_id, is_active=True)
    
    # 해당 감정에 대한 추천 장르들 가져오기 (우선순위 순)
    recommendations = EmotionGenreRecommendation.objects.filter(
        emotion=emotion
    ).select_related('genre').order_by('priority')
    
    # 사용자의 과거 선택 이력 고려 (향후 개인화를 위한 기반)
    user_history = UserEmotionEntry.objects.filter(
        user=request.user,
        emotion=emotion
    ).prefetch_related('selected_genres').order_by('-date')[:5]  # 최근 5개
    
    context = {
        'emotion': emotion,
        'recommendations': recommendations,
        'user_history': user_history,
        'page_title': f'{emotion.name} 감정을 위한 맞춤 추천'
    }
    
    return render(request, 'emotions/recommendation_results.html', context)


@login_required
@require_http_methods(["POST"])
def save_emotion_entry(request):
    """감정 기록 저장"""
    try:
        data = json.loads(request.body)
        emotion_id = data.get('emotion_id')
        selected_genre_ids = data.get('selected_genres', [])
        note = data.get('note', '')
        intensity = data.get('intensity', 5)
        entry_date = data.get('date', date.today().isoformat())
        
        # 감정 검증
        emotion = get_object_or_404(Emotion, id=emotion_id, is_active=True)
        
        # 날짜 파싱
        if isinstance(entry_date, str):
            from datetime import datetime
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        
        # 기존 기록이 있으면 업데이트, 없으면 생성
        entry, created = UserEmotionEntry.objects.get_or_create(
            user=request.user,
            date=entry_date,
            defaults={
                'emotion': emotion,
                'note': note,
                'intensity': intensity
            }
        )
        
        if not created:
            # 기존 기록 업데이트
            entry.emotion = emotion
            entry.note = note
            entry.intensity = intensity
            entry.save()
        
        # 선택된 장르들 설정
        if selected_genre_ids:
            genres = Genre.objects.filter(id__in=selected_genre_ids)
            entry.selected_genres.set(genres)
        else:
            entry.selected_genres.clear()
        
        action = '업데이트' if not created else '저장'
        
        return JsonResponse({
            'success': True,
            'message': f'오늘의 감정이 {action}되었습니다!',
            'entry_id': entry.id
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'저장 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
def user_emotion_history(request):
    """사용자 감정 히스토리 페이지"""
    entries = UserEmotionEntry.objects.filter(
        user=request.user
    ).select_related('emotion').prefetch_related('selected_genres').order_by('-date')
    
    # 페이지네이션 (선택사항)
    from django.core.paginator import Paginator
    paginator = Paginator(entries, 20)  # 페이지당 20개
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 간단한 통계
    total_entries = entries.count()
    if total_entries > 0:
        # 가장 많은 감정
        from django.db.models import Count
        most_common_emotion = entries.values('emotion__name', 'emotion__emoji').annotate(
            count=Count('emotion')
        ).order_by('-count').first()
        
        # 이번 달 기록 수
        from datetime import datetime
        current_month = datetime.now().month
        current_year = datetime.now().year
        this_month_count = entries.filter(
            date__month=current_month,
            date__year=current_year
        ).count()
    else:
        most_common_emotion = None
        this_month_count = 0
    
    context = {
        'page_obj': page_obj,
        'total_entries': total_entries,
        'most_common_emotion': most_common_emotion,
        'this_month_count': this_month_count,
        'page_title': '감정 기록 히스토리'
    }
    
    return render(request, 'emotions/emotion_history.html', context)


def api_emotions(request):
    """감정 목록 API (AJAX용)"""
    emotions = Emotion.objects.filter(is_active=True).order_by('order', 'name')
    data = []
    
    for emotion in emotions:
        data.append({
            'id': emotion.id,
            'name': emotion.name,
            'emoji': emotion.emoji,
            'description': emotion.description,
            'sub_description': emotion.sub_description,
            'color_code': emotion.color_code
        })
    
    return JsonResponse({'emotions': data})


def api_recommendations(request, emotion_id):
    """추천 결과 API (AJAX용)"""
    emotion = get_object_or_404(Emotion, id=emotion_id, is_active=True)
    recommendations = EmotionGenreRecommendation.objects.filter(
        emotion=emotion
    ).select_related('genre').order_by('priority')
    
    data = {
        'emotion': {
            'id': emotion.id,
            'name': emotion.name,
            'emoji': emotion.emoji,
            'description': emotion.description
        },
        'recommendations': []
    }
    
    for rec in recommendations:
        data['recommendations'].append({
            'genre': {
                'id': rec.genre.id,
                'name': rec.genre.name,
                'icon': rec.genre.icon,
                'description': rec.genre.description,
                'category': rec.genre.category
            },
            'priority': rec.priority,
            'reason': rec.reason,
            'match_percentage': rec.match_percentage
        })
    
    return JsonResponse(data)