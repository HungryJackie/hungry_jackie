# characters/management/commands/setup_media_images.py

import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'static의 기본 이미지들을 media 폴더로 복사합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--image-file',
            type=str,
            default='default_character.jpg',
            help='복사할 이미지 파일명',
        )

    def handle(self, *args, **options):
        image_filename = options['image_file']
        
        # 경로 설정
        static_image_path = os.path.join(
            settings.BASE_DIR, 
            'static', 
            'images', 
            'characters', 
            image_filename
        )
        
        media_image_path = os.path.join(
            settings.MEDIA_ROOT,
            image_filename
        )
        
        # static 파일 존재 확인
        if not os.path.exists(static_image_path):
            self.stdout.write(
                self.style.ERROR(f'static 이미지 파일을 찾을 수 없습니다: {static_image_path}')
            )
            return
        
        # media 디렉터리 생성 (없는 경우)
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        
        try:
            # 파일 복사
            shutil.copy2(static_image_path, media_image_path)
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ 이미지가 성공적으로 복사되었습니다!')
            )
            self.stdout.write(f'  From: {static_image_path}')
            self.stdout.write(f'  To: {media_image_path}')
            
            # 캐릭터들 업데이트
            self.update_characters(image_filename)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'파일 복사 중 오류 발생: {str(e)}')
            )

    def update_characters(self, image_filename):
        """기본 캐릭터들의 이미지 경로 업데이트"""
        from characters.models import Character
        
        # 이미지가 없는 시스템 캐릭터들 업데이트
        characters_to_update = Character.objects.filter(
            creator__username='system_default',
            character_image__isnull=True
        ) | Character.objects.filter(
            creator__username='system_default',
            character_image=''
        )
        
        updated_count = 0
        for character in characters_to_update:
            character.character_image = image_filename
            character.save()
            updated_count += 1
            self.stdout.write(f'  ✓ {character.name} 이미지 설정됨')
        
        self.stdout.write(
            self.style.SUCCESS(f'\n총 {updated_count}개 캐릭터의 이미지가 설정되었습니다!')
        )
        
        self.stdout.write(
            self.style.WARNING(f'\n이제 다음 URL에서 확인해보세요:')
        )
        self.stdout.write('http://127.0.0.1:8000/characters/')