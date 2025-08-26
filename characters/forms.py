from django import forms
from django.core.exceptions import ValidationError
from PIL import Image
import os
from .models import Character, CharacterRating
from emotions.models import Genre

class CharacterCreateForm(forms.ModelForm):
    """캐릭터 생성 폼"""
    
    class Meta:
        model = Character
        fields = [
            'name', 'genre', 'description', 'personality', 
            'background_story', 'speaking_style', 'tags', 
            'character_image', 'visibility'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '캐릭터 이름을 입력해주세요',
                'maxlength': 50,
            }),
            'genre': forms.Select(attrs={
                'class': 'form-select',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '캐릭터에 대한 간단한 설명을 작성해주세요',
                'rows': 3,
            }),
            'personality': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '성격, 특징, 행동 패턴 등을 자세히 작성해주세요',
                'rows': 4,
            }),
            'background_story': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '캐릭터의 과거, 경험, 설정 등을 작성해주세요',
                'rows': 4,
            }),
            'speaking_style': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '말투, 억양, 자주 사용하는 표현 등을 작성해주세요',
                'rows': 3,
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '태그1, 태그2, 태그3 (쉼표로 구분)',
            }),
            'character_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 장르 선택지
        self.fields['genre'].queryset = Genre.objects.all().order_by('name')
        
        # 필수 필드
        for field_name in ['name', 'genre', 'description', 'personality']:
            if field_name in self.fields:
                self.fields[field_name].required = True
    
    def clean_character_image(self):
        """이미지 파일 검증"""
        image = self.cleaned_data.get('character_image')
        
        if image:
            # 파일 크기 검증 (2MB 제한)
            if image.size > 2 * 1024 * 1024:
                raise ValidationError('이미지 파일 크기는 2MB 이하여야 합니다.')
            
            # 파일 확장자 검증
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('JPG, PNG, GIF, WebP 형식의 이미지만 업로드 가능합니다.')
        
        return image
    
    def clean_name(self):
        """캐릭터 이름 검증"""
        name = self.cleaned_data.get('name')
        
        if not name:
            raise ValidationError('캐릭터 이름을 입력해주세요.')
        
        if len(name) < 2:
            raise ValidationError('캐릭터 이름은 2자 이상이어야 합니다.')
        
        # 동일한 사용자의 캐릭터 이름 중복 검증
        if self.user:
            existing = Character.objects.filter(
                creator=self.user, 
                name=name
            )
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise ValidationError('이미 동일한 이름의 캐릭터가 있습니다.')
        
        return name

