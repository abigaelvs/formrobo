from django.forms import ModelForm
from .models import Section, SCHEDULE_TYPE_CHOICES

from django.contrib.auth import get_user, get_user_model

# django celery beat models
from django_celery_beat.models import PeriodicTask, IntervalSchedule, ClockedSchedule, CrontabSchedule, SolarSchedule, SOLAR_SCHEDULES

from django import forms


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'url', 'schedule_type']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g Presence Form'
            }),
            'url': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g https://forms.gle/bfy9oyXo4P5mjfUs9'
            }),
            'schedule_type': forms.Select(
                choices=SCHEDULE_TYPE_CHOICES,
                attrs={
                    'class': 'form-control',
            })
        }


class PeriodicTaskForm(forms.Form):
    start_time = forms.CharField(required=False, widget=forms.TextInput(
        attrs={
            'type': 'datetime-local',
            'class': 'form-control',
            'placeholder': 'e.g 2021-04-09 17:22:31',
        }
    ))

    one_off = forms.BooleanField(required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input',
            }
    ))


class IntervalScheduleForm(forms.ModelForm, PeriodicTaskForm):
    class Meta:
        PERIOD_CHOICES = (
            ('days', 'Days'),
            ('hour', 'Hour'),
            ('minutes', 'Minutes'),
            ('seconds', 'Seconds'),
            ('microseconds', 'Microseconds')
        )
        model = IntervalSchedule
        fields = '__all__'
        widgets = {
            'every': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g 5 (number)'
            }),
            'period': forms.Select(
                choices=PERIOD_CHOICES,
                attrs={
                    'class': 'form-control',
            })
        }


class ClockedScheduleForm(forms.ModelForm, PeriodicTaskForm):
    class Meta:
        model = ClockedSchedule
        fields = '__all__'
        widgets = {
            'clocked_time': forms.DateTimeInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g 2021-04-09 17:22:31'
            })
        }


class CrontabScheduleForm(forms.ModelForm, PeriodicTaskForm):
    class Meta:
        DAY_OF_WEEK_CHOICES = (
            ('*', '*'),
            (1, 'Monday'),
            (2, 'Tuesday'),
            (3, 'Wednesday'),
            (4, 'Thursday'),
            (5, 'Friday'),
            (6, 'Saturday'),
            (7, 'Sunday')
        )

        MONTH_OF_YEAR_CHOICES = (
            ('*', '*'),
            (1, 'January'),
            (2, 'February'),
            (3, 'March'),
            (4, 'April'),
            (5, 'May'),
            (6, 'June'),
            (7, 'July'),
            (8, 'August'),
            (9, 'September'),
            (10, 'October'),
            (11, 'November'),
            (12, 'December')
        )
        model = CrontabSchedule
        fields = '__all__'
        widgets = {
            'hour': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'value': '*',
                    'placeholder': 'Cron hour to Run. Use "*" for "all". (Example: "0,30")'
            }),
            'minute': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'value': '*',
                    'placeholder': 'Cron minute to Run. Use "*" for "all". (Example: "0,30")'
            }),
            'day_of_week': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Cron day of week to Run. Use "*" for "all". (Example: "0,30")'
            }),
            'day_of_month': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'value': '*',
                    'placeholder': 'Cron day of month to Run. Use "*" for "all". (Example: "0,30")'
            }),
            'month_of_year': forms.TextInput(
                attrs={
                    'class': 'form-select',
                    'value': '*',
                    'placeholder': 'Cron month of year to Run. Use "*" for "all". (Example: "0,30")'
            }),
            'timezone': forms.Select(
                attrs={
                    'class': 'form-select'
            })
        }


class SolarScheduleForm(forms.ModelForm, PeriodicTaskForm):
    class Meta:
        model = SolarSchedule
        fields = '__all__'
        widgets = {
            'latitude':forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Run the task when the event happens at this latitude'
                }),
            'longitude': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Run the task when the event happens at this longitude'
                }),
            'event': forms.Select(
                choices=SOLAR_SCHEDULES,
                attrs={
                    'class': 'form-control'
                }),
        }