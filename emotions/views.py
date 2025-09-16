# emotions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date, datetime
from django.core.paginator import Paginator
import json
import calendar

from .models import Emotion, Genre, EmotionGenreRecommendation, UserEmotionEntry


def emotion_selection(request):
    """감정 선택 페이지"""
    emotions = Emotion.objects.filter(is_active=True).order_by('order', 'name')
    
    # 오늘 이미 기록된 감정이 있는지 확인
    today_entry = None
    if request.user.is_authenticated:
        today_entry = UserEmotionEntry.objects.filter(
            user=request.user,
            date=date.today()
        ).select_related('emotion').prefetch_related('selected_genres').first()
    
    context = {
        'emotions': emotions,
        'page_title': '오늘 기분이 어떠신가요?' if not today_entry else '오늘의 감정을 수정해보세요',
        'today_entry': today_entry,
        'is_edit_mode': bool(today_entry),
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
        note = data.get('note', '')
        selected_genre_ids = data.get('selected_genres', [])  # 추가
        entry_date = data.get('date', date.today().isoformat())
        
        # 감정 검증
        emotion = get_object_or_404(Emotion, id=emotion_id, is_active=True)
        
        # 날짜 파싱
        if isinstance(entry_date, str):
            entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        
        # 기존 기록이 있으면 업데이트, 없으면 생성
        entry, created = UserEmotionEntry.objects.get_or_create(
            user=request.user,
            date=entry_date,
            defaults={
                'emotion': emotion,
                'note': note,
                'intensity': 5  # 기본값
            }
        )
        
        if not created:
            # 기존 기록 업데이트
            entry.emotion = emotion
            entry.note = note
            entry.save()
        
        # 선택된 장르들 설정 (이미 있던 장르는 유지)
        if selected_genre_ids:
            genres = Genre.objects.filter(id__in=selected_genre_ids)
            entry.selected_genres.add(*genres)
        
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
def emotion_calendar(request):
    """감정 캘린더 페이지"""
    # 현재 연월 파라미터 처리
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))
    
    # 해당 월의 감정 기록들 가져오기
    entries = UserEmotionEntry.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).select_related('emotion').order_by('date')
    
    # 날짜별로 정리
    entries_by_date = {entry.date.day: entry for entry in entries}
    
    # 캘린더 데이터 생성
    cal = calendar.monthcalendar(year, month)
    
    # 캘린더 주차별 데이터 가공 (템플릿에서 쉽게 사용하도록)
    calendar_weeks_with_entries = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': 0, 'entry': None})
            else:
                entry = entries_by_date.get(day)
                week_data.append({'day': day, 'entry': entry})
        calendar_weeks_with_entries.append(week_data)
    
    # 이전/다음 달 계산
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
        
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    # 월 이름
    month_names = [
        '', '1월', '2월', '3월', '4월', '5월', '6월',
        '7월', '8월', '9월', '10월', '11월', '12월'
    ]
    
    context = {
        'year': year,
        'month': month,
        'month_name': month_names[month],
        'calendar_weeks_with_entries': calendar_weeks_with_entries,  # 가공된 데이터
        'entries_count': len(entries_by_date),
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': date.today(),
    }
    
    return render(request, 'emotions/emotion_calendar.html', context)

@login_required
def emotion_detail(request, entry_id):
    """감정 기록 상세 정보 (AJAX)"""
    entry = get_object_or_404(
        UserEmotionEntry,
        id=entry_id,
        user=request.user
    )
    
    data = {
        'date': entry.date.strftime('%Y-%m-%d'),
        'emotion': {
            'name': entry.emotion.name,
            'emoji': entry.emotion.emoji,
            'description': entry.emotion.description
        },
        'note': entry.note,
        'created_at': entry.created_at.strftime('%H:%M')
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def update_emotion_entry(request, entry_id):
    """감정 기록 수정"""
    entry = get_object_or_404(
        UserEmotionEntry,
        id=entry_id,
        user=request.user
    )
    
    try:
        data = json.loads(request.body)
        note = data.get('note', '')
        
        entry.note = note
        entry.save()
        
        return JsonResponse({
            'success': True,
            'message': '감정 기록이 수정되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'수정 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def delete_emotion_entry(request, entry_id):
    """감정 기록 삭제"""
    entry = get_object_or_404(
        UserEmotionEntry,
        id=entry_id,
        user=request.user
    )
    
    try:
        entry.delete()
        
        return JsonResponse({
            'success': True,
            'message': '감정 기록이 삭제되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'삭제 중 오류가 발생했습니다: {str(e)}'
        })


@login_required
def user_emotion_history(request):
    """사용자 감정 히스토리 페이지"""
    entries = UserEmotionEntry.objects.filter(
        user=request.user
    ).select_related('emotion').prefetch_related('selected_genres').order_by('-date')
    
    # 페이지네이션
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


# API 엔드포인트들 (기존 유지)
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
                'description': rec.genre.description,
                'category': rec.genre.category
            },
            'priority': rec.priority,
            'reason': rec.reason,
            'match_percentage': rec.match_percentage
        })
    
    return JsonResponse(data)