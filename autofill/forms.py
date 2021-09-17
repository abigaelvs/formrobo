from django.forms import ModelForm
from .models import Section, SCHEDULE_TYPE_CHOICES

# django celery beat models
from django_celery_beat.models import IntervalSchedule, PeriodicTask, ClockedSchedule, CrontabSchedule, SolarSchedule, SOLAR_SCHEDULES

from django import forms

from django.core.exceptions import ValidationError

import json

from .utils import get_fields

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'url']
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
            })
        }
    
    def process(self, user):
        name = self.cleaned_data.get("name")
        url = self.cleaned_data.get("url")

        section = Section.objects.get_section_by_name(name)

        if section.exists():
            raise ValueError("Section with this name is already available")

        fields = get_fields(url)

        if not fields:
            raise ValueError("Form URL is not valid")

        return Section.objects.add_section(name, url, user)


class UpdateSectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name']
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g Presence Form'
            })
        }
    
    def process(self, section_id):
        name = self.cleaned_data.get("name")

        section = Section.objects.get_section_by_name(name)

        if section.exists():
            raise ValueError("Section with this name is already available")

        return Section.objects.update_section(section_id, name)


class PeriodicTaskForm(forms.Form):
    start_time = forms.CharField(required=False, widget=forms.TextInput(
        attrs={
            'class': 'form-control',
            'placeholder': 'e.g 2021-04-09 17:22:31',
        }
    ))

    one_off = forms.BooleanField(required=False, widget=forms.CheckboxInput(
            attrs={
                'class': 'form-check-input',
            }
    ))

    def check_task_type(self, section: Section, new_schedule: str) -> str:
        if section.task.interval:
            if "Interval" != new_schedule:
                section.task.interval.delete()
                
        elif section.task.clocked:
            if "Clocked" != new_schedule:
                section.task.clocked.delete()
        
        elif section.task.crontab:
            if "Crontab" != new_schedule:
                section.task.crontab.delete()

        elif section.taks.solar:
            if "Solar" != new_schedule:
                section.task.solar.delete()

    def check_task(section: Section):
        if section.task:
            return True
        return False


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

    def process(self, section_id, user):
        every = self.cleaned_data.get("every")
        period = self.cleaned_data.get("period")
        start_time = self.cleaned_data.get("start_time")
        one_off = self.cleaned_data.get("one_off")

        section = Section.objects.get(pk=int(section_id))

        if PeriodicTaskForm.check_task(section):
            self.check_task_type(section, "Interval")
        
        try:
            interval = Section.objects.add_interval(every, period)

            try:
                periodic_task = Section.objects.add_periodic_task({
                    "name": f"{user} {section.name} Task",
                    "schedule_type": "Interval",
                    "interval": interval,
                    "start_time": start_time,
                    "one_off": one_off,
                    "args": json.dumps([section.id]),
                })
                
                try:
                    updated_section = Section.objects.add_task(section, periodic_task, "Interval")
                    return updated_section

                except Exception as e:
                    return e

            except Exception as e:
                return e

        except Exception as e:
            return e

        


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

    def process(self, section_id, user):
        clocked_time = self.cleaned_data.get('clocked_time')
        start_time = self.cleaned_data.get('start_time')

        section = Section.objects.get(pk=int(section_id))

        if PeriodicTaskForm.check_task(section):
            self.check_task_type(section, "Clocked")

        try:
            clocked = Section.objects.add_clocked(clocked_time)

            try:
                periodic_task = Section.objects.add_periodic_task({
                    "name": f"{user} {section.name} Task",
                    "schedule_type": "Clocked",
                    "clocked": clocked,
                    "start_time": start_time,
                    "args": json.dumps([section.id]),
                })

                try:
                    updated_section = Section.objects.add_task(section, periodic_task, "Clocked")
                    return updated_section
                
                except Exception as e:
                    return e

            except Exception as e:
                return e

        except Exception as e:
            return e


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
    
    def process(self, section_id, user):
        hour = self.cleaned_data.get("hour")
        minute = self.cleaned_data.get("minute")
        day_of_week = self.cleaned_data.get("day_of_week")
        day_of_month = self.cleaned_data.get("day_of_month")
        month_of_year = self.cleaned_data.get("month_of_year")
        timezone = self.cleaned_data.get("timezone")
        start_time = self.cleaned_data.get("start_time")
        one_off = self.cleaned_data.get("one_off")

        section = Section.objects.get(pk=int(section_id))

        if PeriodicTaskForm.check_task(section):
            self.check_task_type(section, "Crontab")

        try:
            crontab = Section.objects.add_crontab({
                "hour": hour,
                "minute": minute,
                "day_of_week": day_of_week,
                "day_of_month": day_of_month,
                "month_of_year": month_of_year,
                "timezone": timezone,
                "start_time": start_time,
                "one_off": one_off
            })

            try:
                periodic_task = Section.objects.add_periodic_task({
                    "name": f"{user} {section.name} Task",
                    "schedule_type": "Crontab",
                    "crontab": crontab,
                    "start_time": start_time,
                    "one_off": one_off,
                    "args": json.dumps([section.id]),
                })

                try:
                    updated_section = Section.objects.add_task(section, periodic_task, "Crontab")
                    return updated_section

                except Exception as e:
                    return e

            except Exception as e:
                return e

        except Exception as e:
            return e


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

    def process(self, section_id, user):
        latitude = self.cleaned_data.get("latitude")
        longitude = self.cleaned_data.get("longitude")
        event = self.cleaned_data.get("event")
        start_time = self.cleaned_data.get("start_time")
        one_off = self.cleaned_data.get("one_off")

        section = Section.objects.get(pk=int(section_id))

        if PeriodicTaskForm.check_task(section):
            self.check_task_type(section, "Solar")

        try:
            solar = Section.objects.add_solar({
                "latitude": latitude,
                "longitude": longitude,
                "event": event
            })

            try:
                periodic_task = Section.objects.add_periodic_task({
                    "name": f"{user} {section.name} Task",
                    "schedule_type": "Solar",
                    "solar": solar,
                    "start_time": start_time,
                    "one_off": one_off,
                    "args": json.dumps([section.id]),
                })

                try:
                    updated_section = Section.objects.add_task(section, periodic_task, "Solar")
                    return updated_section

                except Exception as e:
                    return e

            except Exception as e:
                return e

        except Exception as e:
            return e