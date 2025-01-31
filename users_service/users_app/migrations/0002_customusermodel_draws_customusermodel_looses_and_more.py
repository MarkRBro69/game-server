# Generated by Django 5.1.4 on 2025-01-29 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customusermodel',
            name='draws',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customusermodel',
            name='looses',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='customusermodel',
            name='rating',
            field=models.IntegerField(default=1000),
        ),
        migrations.AddField(
            model_name='customusermodel',
            name='wins',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='customusermodel',
            name='password',
            field=models.CharField(max_length=128),
        ),
    ]
