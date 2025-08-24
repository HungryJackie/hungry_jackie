from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Setup social authentication apps automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset all existing social apps before creating new ones',
        )
        parser.add_argument(
            '--provider',
            type=str,
            help='Setup only specific provider (google, kakao, naver)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Setting up social authentication apps...'))
        
        # 사이트 설정
        self.setup_site()
        
        # 기존 앱들 삭제 (옵션)
        if options['reset']:
            self.reset_social_apps()

        # 소셜 앱들 생성
        self.create_social_apps(options.get('provider'))
        
        # 최종 결과 표시
        self.show_final_status()

    def setup_site(self):
        """Django Sites 프레임워크 설정"""
        try:
            site = Site.objects.get(pk=1)
            site.domain = '127.0.0.1:8000'
            site.name = 'Hungry Jackie'
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Site updated: {site.name} ({site.domain})'))
        except Site.DoesNotExist:
            site = Site.objects.create(
                pk=1,
                domain='127.0.0.1:8000',
                name='Hungry Jackie'
            )
            self.stdout.write(self.style.SUCCESS(f'Site created: {site.name} ({site.domain})'))
        return site

    def reset_social_apps(self):
        """기존 소셜 앱들 삭제"""
        deleted_count = SocialApp.objects.all().count()
        SocialApp.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing social apps'))

    def create_social_apps(self, specific_provider=None):
        """소셜 앱들 생성"""
        # 지원하는 소셜 제공자들
        social_providers = [
            {
                'provider': 'google',
                'name': 'Google',
                'client_id_env': 'GOOGLE_CLIENT_ID',
                'secret_env': 'GOOGLE_SECRET_KEY'
            },
            {
                'provider': 'kakao',
                'name': 'Kakao',
                'client_id_env': 'KAKAO_CLIENT_ID',
                'secret_env': 'KAKAO_SECRET_KEY'
            },
            {
                'provider': 'naver',
                'name': 'Naver',
                'client_id_env': 'NAVER_CLIENT_ID',
                'secret_env': 'NAVER_SECRET_KEY'
            }
        ]

        # 특정 제공자만 설정하는 경우
        if specific_provider:
            social_providers = [p for p in social_providers if p['provider'] == specific_provider]
            if not social_providers:
                self.stdout.write(self.style.ERROR(f'Unknown provider: {specific_provider}'))
                return

        site = Site.objects.get(pk=1)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for provider_config in social_providers:
            result = self.create_single_app(provider_config, site)
            if result == 'created':
                created_count += 1
            elif result == 'updated':
                updated_count += 1
            else:
                skipped_count += 1

        # 결과 요약 저장
        self.setup_results = {
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count
        }

    def create_single_app(self, provider_config, site):
        """개별 소셜 앱 생성"""
        client_id = os.getenv(provider_config['client_id_env'])
        secret = os.getenv(provider_config['secret_env'], '')

        if not client_id:
            self.stdout.write(
                self.style.ERROR(
                    f'{provider_config["name"]} - No {provider_config["client_id_env"]} in .env file'
                )
            )
            return 'skipped'

        try:
            social_app, created = SocialApp.objects.get_or_create(
                provider=provider_config['provider'],
                defaults={
                    'name': provider_config['name'],
                    'client_id': client_id,
                    'secret': secret,
                }
            )
            
            if created:
                social_app.sites.add(site)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created {provider_config["name"]} app'
                    )
                )
                return 'created'
            else:
                # 기존 앱 업데이트
                social_app.client_id = client_id
                social_app.secret = secret
                social_app.save()
                social_app.sites.add(site)
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated {provider_config["name"]} app'
                    )
                )
                return 'updated'
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'Error setting up {provider_config["name"]}: {e}'
                )
            )
            return 'skipped'

    def show_final_status(self):
        """최종 설정 상태 표시"""
        results = getattr(self, 'setup_results', {'created': 0, 'updated': 0, 'skipped': 0})
        
        self.stdout.write(self.style.SUCCESS(f'\nSetup Summary:'))
        self.stdout.write(f'   Created: {results["created"]} apps')
        self.stdout.write(f'   Updated: {results["updated"]} apps')
        self.stdout.write(f'   Skipped: {results["skipped"]} apps')
        
        # 활성 앱들 목록 표시
        active_apps = SocialApp.objects.all()
        if active_apps:
            self.stdout.write(f'\nActive Social Apps:')
            for app in active_apps:
                self.stdout.write(f'   - {app.name} ({app.provider})')
        
        # 도움말 메시지
        if results['skipped'] > 0:
            self.stdout.write(self.style.WARNING(f'\nTips:'))
            self.stdout.write(f'   - Add missing API keys to .env file')
            self.stdout.write(f'   - Run command again after adding keys')
            self.stdout.write(f'   - Use --provider option for specific setup')

        self.stdout.write(self.style.SUCCESS(f'\nSocial apps setup completed!'))
        self.stdout.write(f'Test at: http://127.0.0.1:8000/accounts/login/')

    def show_env_example(self):
        """환경변수 예시 표시"""
        self.stdout.write(self.style.WARNING(f'\n.env file example:'))
        example_env = """
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_SECRET_KEY=your_google_secret_key
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_SECRET_KEY=your_kakao_secret_key
NAVER_CLIENT_ID=your_naver_client_id
NAVER_SECRET_KEY=your_naver_secret_key
"""
        self.stdout.write(example_env.strip())