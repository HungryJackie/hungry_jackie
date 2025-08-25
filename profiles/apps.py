from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiles'

    def ready(self):
        """앱이 준비되면 signals 임포트"""
        import profiles.models  # signals가 등록되도록 모델 임포트