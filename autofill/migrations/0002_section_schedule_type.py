# Generated by Django 3.1.7 on 2021-04-09 04:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autofill', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='section',
            name='schedule_type',
            field=models.CharField(blank=True, choices=[('Interval', 'Interval'), ('Clocked', 'Clocked'), ('Crontab', 'Crontab'), ('Solar', 'Solar')], max_length=20, null=True),
        ),
    ]
