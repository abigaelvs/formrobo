from django.contrib import auth
from django.contrib.auth.models import User
from django.shortcuts import render, redirect



# django views
from django.views.generic import View, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

# django auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm

# django exceptions
from django.core.exceptions import ObjectDoesNotExist

# django messages
from django.contrib import messages

# django celery beat
from django_celery_beat.models import ClockedSchedule, CrontabSchedule, \
    IntervalSchedule, SolarSchedule, PeriodicTask


# app models
from .models import Section, Question, Answer, Log

# app forms
from .forms import SectionForm, CrontabScheduleForm, IntervalScheduleForm, ClockedScheduleForm, SolarScheduleForm

from .utils import submit_form, check_form


import json


def index(request):
    """ 
    This is the homepage view of the application 
    There's no models and queryset on this view
    """
    return redirect('users:login')


@login_required(login_url='autofill:login')
def dashboard(request):
    """ List of user section and logs """
    logs = Log.objects.filter(user=request.user).order_by('-date')
    submitted_form = logs.count()
    succesfully_submitted = Log.objects.filter(user=request.user, status='Success').count()
    failed_to_submit = Log.objects.filter(user=request.user, status='Failed').count()
    sections = Section.objects.filter(user=request.user).order_by('-date_created')[:4]

    context = {
        'logs': logs,
        'sections': sections,
        'submitted_form': submitted_form,
        'succesfully_submitted': succesfully_submitted,
        'failed_to_submit': failed_to_submit
    }
    return render(request, 'autofill/dashboard.html', context)



class SectionView(ListView, LoginRequiredMixin):
    """ List of user section, filtered by user """
    def get(self, *args, **kwargs):
        sections = Section.objects.filter(user=self.request.user)
        enabled_sections = Section.objects.filter(user=self.request.user, task__enabled=True).count()
        disabled_sections = Section.objects.filter(user=self.request.user, task__enabled=False).count()
        context = {
            'sections': sections,
            'sections_count': sections.count(),
            'enabled_sections': enabled_sections,
            'disabled_sections': disabled_sections
        }
        return render(self.request, 'autofill/sections.html', context)


class LogView(ListView, LoginRequiredMixin):
    """ List of all user logs """
    def get(self, *args, **kwargs):
        logs = Log.objects.filter(user=self.request.user)
        context = {
            'logs': logs,
        }
        return render(self.request, 'autofill/logs.html', context)


class DetailSectionView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        try:
            section = Section.objects.get(pk=kwargs['pk'])

            answers = Answer.objects.filter(question__section=section)
            context = {
                'section': section,
                'answers': answers,
            }
            return render(self.request, 'autofill/detail-section.html', context)
        except ObjectDoesNotExist:
            return redirect('autofill:dashboard')


class LogDetailView(DetailView, LoginRequiredMixin):
    """ Detailed information about user log """
    model = Log
    template_name = 'autofill/log-detail.html'
    context_object_name = 'log'


class AddSectionView(View, LoginRequiredMixin):
    """
    View to add new section (forms)
    
    After user submit the section form, user will be
    redirected to selected schedule type view
    
    Add Form data to database table Formulir

    1. Scrape link that user input to the formulir form
    2. Scan whole form
    3. Grab all the field class
    4. Loop trough all the fields and specify the formulir type
    5. Get the field question
    6. Save the data into database table pertanyaan
    """
    def get(self, *args, **kwargs):
        form = SectionForm()

        context = {
            'form': form,
        }
        return render(self.request, 'autofill/add-section.html', context)

    def post(self, *args, **kwargs):
        form = SectionForm(self.request.POST or None)
        if form.is_valid():
            name = form.cleaned_data['name']
            url = form.cleaned_data['url']
            schedule_type = form.cleaned_data['schedule_type']

            section = Section.objects.filter(name=name)

            if section.exists():
                messages.warning(self.request, 'Form dengan nama yang sama sudah ada. Ganti nama atau hapus form sebelumnya')
                return redirect('autofill:add-section')
            else:
                # save formulir form data
                section = Section(
                    user=self.request.user,
                    name=name,
                    url=url,
                    schedule_type=schedule_type
                )
                section.save()

            # switch case statement in python
            # switch case statement for interval time
            def schedule(argument):
                def interval():
                    return redirect('autofill:add-interval', section.pk)
                def clocked():
                    return redirect('autofill:add-clocked', section.pk)
                def crontab():
                    return redirect('autofill:add-crontab', section.pk)
                def solar():
                    return redirect('autofill:add-solar', section.pk)

                switcher = {
                    'Interval': interval(),
                    'Clocked': clocked(),
                    'Crontab': crontab(),
                    'Solar': solar()
                }
                func = switcher.get(argument, lambda: 'Invalid Schedule type')
                return func
            
            return schedule(schedule_type)
        return redirect('autofill:dashboard')


class EditSectionView(View, LoginRequiredMixin):
    """ View to edit section name, url, or schedule type """
    def get(self, *args, **kwargs):
        section = Section.objects.get(pk=kwargs['pk'])
        form = SectionForm(instance=section)
        context = {
            'form': form
        }
        return render(self.request, 'autofill/edit-section.html', context)
    def post(self, *args, **kwargs):
        section = Section.objects.get(pk=kwargs['pk'])
        form = SectionForm(self.request.POST, instance=section)

        if form.is_valid():
            form.save()
            section.task.name = f'{self.request.user} {section.name} Task'
            section.task.save()
            return redirect('autofill:detail-section', kwargs['pk'])
        

class AddIntervalView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        try:
            section = Section.objects.get(pk=kwargs['pk'])
            try:
                form = IntervalScheduleForm(instance=section.task.interval)
            except Exception:
                form = IntervalScheduleForm()
            context = {
                'section': section,
                'form': form,
            }
            return render(self.request, 'autofill/add-interval.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active section right now')
            return redirect('autofill:dashboard')
    def post(self, *args, **kwargs):
        form = IntervalScheduleForm(self.request.POST or None)

        if form.is_valid():
            every = form.cleaned_data['every']
            period = form.cleaned_data['period']
            start_time = form.cleaned_data['start_time']
            one_off = form.cleaned_data['one_off']
           
            interval_schedule = IntervalSchedule(
                every=every,
                period=period
            )
            section = Section.objects.get(pk=kwargs['pk'])

            if section.task:
                if section.task.interval:
                    section.task.interval.every = every
                    section.task.interval.period = period
                    section.task.interval.save()
                    section.task.start_time = (start_time if start_time else None)
                    section.task.one_off = one_off
                    section.task.save()
                    messages.success(self.request, 'Form Schedule successfully changed')
                else:
                    enabled = section.task.enabled
                    section.task.delete()
                    interval_schedule.save()
                    periodic_task = PeriodicTask(
                        name=f'{self.request.user} {section.name} Task',
                        task='send_form_task',
                        interval=interval_schedule,
                        start_time=(start_time if start_time else None),
                        one_off=one_off,
                        args=json.dumps([section.id]),
                        enabled=enabled
                    )
                    periodic_task.save()
                    section.task = periodic_task
                    section.save()
                    messages.success(self.request, 'Form Schedule successfully changed')
            else:
                interval_schedule.save()
                periodic_task = PeriodicTask(
                    name=f"{self.request.user} {section.name} Task",
                    task='send_form_task',
                    enabled=False,
                    interval=interval_schedule,
                    start_time=(start_time if start_time else None),
                    one_off=one_off,
                    args=json.dumps([section.id])
                )
                periodic_task.save()
                section.task = periodic_task
                section.save()

                check_form(section.id, section.url)

        return redirect('autofill:detail-section', kwargs['pk'])


class AddClockedView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        try:
            section = Section.objects.get(pk=kwargs['pk'])
            try:
                form = ClockedScheduleForm(instance=section.task.clocked)
            except Exception:
                form = ClockedScheduleForm()
            context = {
                'section': section,
                'form': form,
            }
            return render(self.request, 'autofill/add-clocked.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active section right now')
            return redirect('autofill:dashboard')
    def post(self, *args, **kwargs):
        form = ClockedScheduleForm(self.request.POST or None)
        if form.is_valid():
            clocked_time = form.cleaned_data['clocked_time']
            start_time = form.cleaned_data['start_time']

            clocked_schedule = ClockedSchedule(
                clocked_time=clocked_time
            )
            
            section = Section.objects.get(pk=kwargs['pk'])

            if section.task:
                if section.task.clocked:
                    section.task.clocked.clocked_time = clocked_time
                    section.task.clocked.save()
                    section.task.start_time = (start_time if start_time else None)
                    section.task.one_off = True
                    section.task.save()
                    messages.success(self.request, 'Form Schedule successfully changed')
                else:
                    enabled = section.task.enabled
                    section.task.delete()
                    clocked_schedule.save()
                    periodic_task = PeriodicTask(
                        name=f'{self.request.user} {section.name} Task',
                        task='send_form_task',
                        clocked=clocked_schedule,
                        start_time=(start_time if start_time else None),
                        one_off=True,
                        args=json.dumps([section.id]),
                        enabled=enabled
                    )
                    periodic_task.save()
                    section.task = periodic_task
                    section.save()
                    messages.success(self.request, 'Form Schedule successfully changed')    
            else:
                clocked_schedule.save()
                periodic_task = PeriodicTask(
                    name=f"{self.request.user} {section.name} Task",
                    task='send_form_task',
                    clocked=clocked_schedule,
                    start_time=(start_time if start_time else None),
                    one_off=True,
                    enabled=False,
                    args=json.dumps([section.id])
                )
                periodic_task.save()
                section.task = periodic_task
                section.save()

                check_form(section.id, section.url)

        return redirect('autofill:detail-section', kwargs['pk'])
        

class AddCrontabView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        try:
            section = Section.objects.get(pk=kwargs['pk'])
            try:
                form = CrontabScheduleForm(instance=section.task.crontab)
            except Exception:
                form = CrontabScheduleForm()
            context = {
                'section': section,
                'form': form,
            }
            return render(self.request, 'autofill/add-crontab.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active section right now')
            return redirect('autofill:dashboard')
    def post(self, *args, **kwargs):
        form = CrontabScheduleForm(self.request.POST or None)

        if form.is_valid():
            hour = form.cleaned_data['hour']
            minute = form.cleaned_data['minute']
            day_of_week = form.cleaned_data['day_of_week']
            day_of_month = form.cleaned_data['day_of_month']
            month_of_year = form.cleaned_data['month_of_year']
            timezone = form.cleaned_data['timezone']
            start_time = form.cleaned_data['start_time']
            one_off = form.cleaned_data['one_off']


            crontab_schedule = CrontabSchedule(
                minute=minute,
                hour=hour,
                day_of_week=day_of_week,
                day_of_month=day_of_month,
                month_of_year=month_of_year,
                timezone=timezone
            )

            section = Section.objects.get(pk=kwargs['pk'])

            if section.task:
                if section.task.crontab:
                    section.task.crontab.minute = minute
                    section.task.crontab.hour = hour
                    section.task.crontab.day_of_week = day_of_week
                    section.task.crontab.day_of_month = day_of_month
                    section.task.crontab.month_of_year = month_of_year
                    section.task.crontab.timezone = timezone
                    section.task.crontab.save()
                    section.task.start_time = (start_time if start_time else None)
                    section.task.one_off = one_off
                    section.task.save()
                    messages.success(self.request, 'Form Schedule successfully changed')
                else:
                    enabled = section.task.enabled
                    section.task.delete()
                    crontab_schedule.save()
                    periodic_task = PeriodicTask(
                        name=f'{self.request.user} {section.name} Task',
                        task='send_form_task',
                        crontab=crontab_schedule,
                        start_time=(start_time if start_time else None),
                        one_off=one_off,
                        args=json.dumps([section.id]),
                        enabled=enabled
                    )
                    periodic_task.save()
                    section.task = periodic_task
                    section.save()
                    messages.success(self.request, 'Form Schedule successfully changed')    
            else:
                crontab_schedule.save()
                periodic_task = PeriodicTask(
                    name=f"{self.request.user} {section.name} Task",
                    task='send_form_task',
                    crontab=crontab_schedule,
                    start_time=(start_time if start_time else None),
                    one_off=one_off,
                    enabled=False,
                    args=json.dumps([section.id])
                )
                periodic_task.save()  
                section.task = periodic_task
                section.save()

                check_form(section.id, section.url)

        return redirect('autofill:detail-section', kwargs['pk'])
        

class AddSolarView(View, LoginRequiredMixin):
    def get(self, *args, **kwargs):
        try:
            section = Section.objects.get(pk=kwargs['pk'])
            try:
                form = SolarScheduleForm(instance=section.task.solar)
            except Exception:
                form = SolarScheduleForm()
            context = {
                'section': section,
                'form': form,
            }
            return render(self.request, 'autofill/add-solar.html', context)
        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active section right now')
            return redirect('autofill:dashboard')
    def post(self, *args, **kwargs):
        form = SolarScheduleForm(self.request.POST or None)
        if form.is_valid():
            latitude = form.cleaned_data['latitude']
            longitude = form.cleaned_data['longitude']
            event = form.cleaned_data['event']
            start_time = form.cleaned_data['start_time']
            one_off = form.cleaned_data['one_off']

            solar_schedule = SolarSchedule(
                latitude=latitude,
                longitude=longitude,
                event=event
            )
            
            section = Section.objects.get(pk=kwargs['pk'])
            
            if section.task:
                if section.task.solar:
                    section.task.solar.latitude = latitude
                    section.task.solar.longitude = longitude
                    section.task.solar.event = event
                    section.task.solar.save()
                    section.task.start_time = (start_time if start_time else None)
                    section.task.one_off = one_off
                    section.task.save()
                    messages.success(self.request, 'Form Schedule successfully changed')
                else:
                    enabled = section.task.enabled
                    section.task.delete()
                    solar_schedule.save()
                    periodic_task = PeriodicTask(
                        name=f'{self.request.user} {section.name} Task',
                        task='send_form_task',
                        solar=solar_schedule,
                        start_time=(start_time if start_time else None),
                        one_off=one_off,
                        args=json.dumps([section.id]),
                        enabled=enabled
                    )
                    periodic_task.save()
                    section.task = periodic_task
                    section.save()
                    messages.success(self.request, 'Form Schedule successfully changed')  
            else:
                solar_schedule.save()
                periodic_task = PeriodicTask(
                    name=f"{self.request.user} {section.name} Task",
                    task='send_form_task',
                    solar=solar_schedule,
                    start_time=(start_time if start_time else None),
                    one_off=one_off,
                    enabled=False,
                    args=json.dumps([section.id])
                )
                periodic_task.save()           
                section.task = periodic_task
                section.save()

            check_form(section.id, section.url)

        return redirect('autofill:detail-section', kwargs['pk'])


@login_required
def form_switch(request, pk):
    """
    This function is for enable and disable form
    """
    section = Section.objects.get(pk=pk)
    if section.task.enabled:
        section.task.enabled = False
    else:
        section.task.enabled = True
    
    section.task.save()
    return redirect('autofill:detail-section', section.pk)


@login_required
def send_form(request, pk):
    """
    The view for manually submit the form
    """
    section = Section.objects.get(pk=pk)
    
    submit = submit_form(id=pk)
    if submit[0] == 'Success':
        messages.success(request, submit[1])
    else:
        messages.warning(request, submit[1])
    
    print(messages)
    return redirect('autofill:detail-section', section.pk)


@login_required 
def regenerate_section(request, pk):
    """
    This is view for regenerating the section
    """
    section = Section.objects.get(pk=pk)
    check_form(section.id, section.url)
    return redirect('autofill:detail-section', section.id)


@login_required
def answers(request, pk):
    """
    This function is for input the answer based on generated answer
    """
    try:
        section = Section.objects.get(pk=pk)
        questions = Question.objects.filter(section=section)
        correct_questions = Question.objects.filter(section=section, correct=True).count()
        false_questions = Question.objects.filter(section=section, correct=False).count()

        kisi_pilihan_ganda = {}
        split_kisi = {}
        for question in questions:
            if question.type == 'Kisi Pilihan Ganda':
                kisi_pilihan_ganda[question.text] = []
                for answer in question.get_answers():
                    kisi_pilihan_ganda[question.text].append(answer.text)
        for kisi in kisi_pilihan_ganda:
            splitted_answer = []
            jawaban = kisi_pilihan_ganda[kisi]
            for jwb in jawaban:
                row, col = jwb.split(',')
                splitted_answer.append(row)
            split_kisi[kisi] = splitted_answer
        if request.method == 'POST':
            for question in questions:
                
                answers = []

                kotak_centang = Answer.objects.filter(question=question, type='Kotak Centang')
                kisi_pilihan_ganda = Answer.objects.filter(question=question, type='Kisi Pilihan Ganda')
                petak_kotak_centang = Answer.objects.filter(question=question, type='Petak Kotak Centang')
                if kotak_centang:
                    for k in kotak_centang:
                        form_data = request.POST.get(k.text)
                        if form_data == k.text:
                            answers.append(form_data)
                elif petak_kotak_centang:
                    for k in petak_kotak_centang:
                        form_data = request.POST.get(k.text)
                        if form_data == k.text:
                            answers.append(form_data)
                elif kisi_pilihan_ganda:
                    for kisi in kisi_pilihan_ganda:
                        row, col = (kisi.text).split(',')
                        form_data = request.POST.get(row)
                        if form_data:
                            answers.append(form_data)
                else:
                    form_data = request.POST.get(question.text)
                    answers.append(form_data)
                for answer in answers:
                    answer_qs = Answer.objects.filter(question=question, text=answer)
                    if answer_qs.exists():
                        for a in answer_qs:
                            a.correct = True
                            a.save()

                            answer_qs2 = Answer.objects.filter(question=question, correct=False)
                            answer_qs2.delete()

                            answer_qs3 = Answer.objects.filter(question=question).count()
                            answer_qs4 = Answer.objects.filter(question=question, correct=True).count()

                            if answer_qs3 == answer_qs4:
                                question.correct = True
                                question.save()
                    else:
                        if answer != None:
                            answer_input = Answer(
                                question=question,
                                text=answer,
                                type=question.type,
                                correct=True
                            )
                            answer_input.save()

                            answer_qs2 = Answer.objects.filter(question=question, correct=False)
                            answer_qs2.delete()

                            answer_qs3 = Answer.objects.filter(question=question).count()
                            answer_qs4 = Answer.objects.filter(question=question, correct=True).count()

                            if answer_qs3 == answer_qs4:
                                question.correct = True
                                question.save()
            return redirect('autofill:detail-section', section.pk)
        context = {
            'section': section,
            'total_questions': questions.count(),
            'split_kisi': split_kisi,
            'correct_questions': correct_questions,
            'false_questions': false_questions
        }
        return render(request, 'autofill/answers.html', context)
    except ObjectDoesNotExist:
        return redirect('autofill:dashboard')


@login_required
def delete_section(request, pk):
    """ This view is for delete the selected section """
    section = Section.objects.get(pk=pk)
    section.delete()
    return redirect('autofill:dashboard')