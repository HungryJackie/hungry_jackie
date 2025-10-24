from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('characters', '0003_alter_usercredit_free_credits'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercredit',
            name='free_credits',
            field=models.IntegerField(default=30, verbose_name='무료 크레딧'),
        ),
    ]