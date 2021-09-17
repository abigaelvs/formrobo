from django.shortcuts import render, redirect

# django class based views
from django.views.generic import View, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

# django auth
from django.contrib.auth.decorators import login_required

# django exceptions
from django.core.exceptions import ObjectDoesNotExist

# django messages
from django.contrib import messages

# autofill app models
from .models import Section, Question, Answer, Log

# app forms
from .forms import (
    SectionForm, UpdateSectionForm, CrontabScheduleForm, 
    IntervalScheduleForm, ClockedScheduleForm, SolarScheduleForm
)

# app utils
from .utils import submit_form, check_form


def index(request):
    """ 
    This is the homepage view (not yet created) of the application 
    There's no models and queryset on this view
    """
    return redirect('users:login')


class DashboardView(LoginRequiredMixin, View):
    """ List of user section and logs """

    template_name = "autofill/dashboard.html"
    form_class = SectionForm
    redirect_url = "autofill:dashboard"

    def get(self, *args, **kwargs):
        context = {
            'sections': Section.objects.get_section_by_user(self.request.user)[:5],
            'logs': Log.objects.get_log_by_user(self.request.user)[:5],
            'submitted_form': Log.objects.get_submitted_form(self.request.user),
            'succesfully_submitted': Log.objects.get_successfuly_submitted(self.request.user),
            'failed_to_submit': Log.objects.get_failed_to_submit(self.request.user),
            "form": self.form_class()
        }
        return render(self.request, self.template_name, context)

    def post(self, *args, **kwargs):
        """POST method to add new Section"""

        form = self.form_class(self.request.POST or None)

        if form.is_valid():
            
            try:
                section = form.process(self.request.user)
                self.request.session[f"q {section.id}"] = check_form(section.url)
                messages.success(self.request, "Successfully add form")
                return redirect(section.get_absolute_url())
            except ValueError as e:
                messages.warning(self.request, e)
            except Exception as e:
                messages.error(self.request, "Error occurs when adding data to database")
                print(e)

        else:
            for e in form.errors:
                messages.error(self.request, f"{e}: {form.errors[e]}")

        return redirect(self.redirect_url)


class SectionView(LoginRequiredMixin, ListView):
    """List of user section, filtered by user"""

    template_name = "autofill/sections.html"
    
    def get(self, *args, **kwargs):
        context = {
            "form": SectionForm(),
            'sections': Section.objects.get_section_by_user(self.request.user),
            'submitted_form': Log.objects.get_submitted_form(self.request.user),
            'enabled_sections': Section.objects.get_enabled_section(self.request.user),
            'disabled_sections': Section.objects.get_disabled_section(self.request.user)
        }
        return render(self.request, self.template_name, context)


class LogView(LoginRequiredMixin, ListView):
    """List of all user logs"""
    template_name = "autofill/logs.html"

    def get(self, *args, **kwargs):
        context = {
            'logs': Log.objects.get_log_by_user(self.request.user),
            "succesfully_submitted": Log.objects.get_successfuly_submitted(self.request.user),
            "failed_to_submit": Log.objects.get_failed_to_submit(self.request.user)
        }
        return render(self.request, self.template_name, context)


class DetailSectionView(LoginRequiredMixin, View):
    """Detail of the section"""

    template_name = "autofill/detail-section.html"
    form_class = UpdateSectionForm
    success_url = "autofill:detail-section"
    failed_url = "autofill:dashboard"

    def get(self, *args, **kwargs):
        try:
            section = Section.objects.get(pk=kwargs["pk"])
            form = self.form_class(instance=section)
            try:
                questions = self.request.session[f"q {kwargs['pk']}"]
            except KeyError:
                questions = Question.objects.get_question_dict(kwargs["pk"])
            
            context = {
                'section': section,
                "form": form,
                "questions": questions,
                "submitted": Log.objects.get_log_by_section(section).count(),
                "successfuly_submitted": Log.objects.get_successfuly_submitted_section(section).count(),
                "failed_submitted": Log.objects.get_failed_submitted_section(section).count(),
            }
            return render(self.request, self.template_name, context)

        except ObjectDoesNotExist:
            messages.error(self.request, "Data not found")
            return redirect(self.failed_url)

    def post(self, *args, **kwargs):
        """POST Method to edit the name of the section"""
        
        form = self.form_class(self.request.POST or None)

        if form.is_valid():
            try:
                form.process(kwargs["pk"])
                messages.success(self.request, "Successfuly update form")
            except ValueError as e:
                messages.warning(self.request, e)
            except Exception as e:
                messages.error(self.request, "Error occurs when adding data to database")
                print(e)
        else:
            for e in form.errors:
                messages.error(self.request, f"{e}: {form.errors[e]}")
        
        return redirect(self.success_url, kwargs["pk"])


# class LogDetailView(LoginRequiredMixin, DetailView):
#     """Detailed information about user log"""

#     model = Log
#     template_name = 'autofill/log-detail.html'
#     context_object_name = 'log'


class AddScheduleView(LoginRequiredMixin, View):
    """View to add new schedule"""

    template_name = "autofill/add-schedule.html"
    redirect_url = "autofill:detail-section"

    def get_form_class(self, schedule_type: str):
        """Helper method to get form class"""

        switcher = {
            "interval": IntervalScheduleForm,
            "clocked": ClockedScheduleForm,
            "crontab": CrontabScheduleForm,
            "solar": SolarScheduleForm
        }

        return switcher.get(schedule_type)

    def get(self, *args, **kwargs):
        section = Section.objects.get(pk=kwargs["pk"])
        schedule_type = kwargs["schedule"]

        context = {
            "schedule_type": schedule_type,
            "form": self.get_form_class(schedule_type),
        }

        return render(self.request, self.template_name, context)

    def post(self, *args, **kwargs):
        schedule_type = kwargs["schedule"]
        form = self.get_form_class(schedule_type)(self.request.POST or None)

        if form.is_valid():
            try:
                result = form.process(kwargs["pk"], self.request.user)
                messages.success(self.request, f"Successfuly set schedule to {schedule_type}")
            except Exception as e:
                messages.error(self.request, "Error occurs when adding data to database")
                print(e)

        else:
            for e in form.errors:
                messages.error(self.request, f"{e}: {form.errors[e]}")

        return redirect(self.redirect_url, kwargs["pk"])


@login_required
def form_switch(request, pk):
    """
    This function is for enable and disable form
    """
    section = Section.objects.get(pk=pk)
    questions = Question.objects.filter(section=section, correct=True)

    if questions.exists():
    
        if section.task.enabled:
            section.task.enabled = False
        else:
            section.task.enabled = True
        
        section.task.save()
        messages.success(request, "Successfully activate auto submit")
    
    else:
        messages.error(request, "Cannot activate the task. Answer all the questions first")

    return redirect('autofill:detail-section', section.pk)


@login_required
def send_form(request, pk):
    """
    The view for manually submit the form
    """
    section = Section.objects.get(pk=pk)
    false = Answer.objects.filter(question__section=section, question__correct=False)
    true = Answer.objects.filter(question__section=section, question__correct=True)

    if false.exists():
        messages.error(request, "Cannot send form. Answer all the question first")

    elif true.exists():
        try:
            submit_form(pk)
            
            messages.success(request, "Successfuly submit form")

        except Exception as e:
            messages.error(request, "Something went wrong")
            print(e)
    else:
        messages.error(request, "Cannot send form. Answer all the question first")

    return redirect('autofill:detail-section', section.pk)


@login_required 
def regenerate_question(request, pk):
    """
    This is view for regenerating the section
    """
    section = Section.objects.get(pk=pk)
    questions = Question.objects.filter(section=section)
    for q in questions:
        answers = Answer.objects.filter(question=q)
        for a in answers:
            a.delete()
        q.delete()
    
    result = check_form(section.url)
    request.session[f"q {pk}"] = result
    messages.success(request, "Successfully Re-generate questions")
    return redirect('autofill:detail-section', section.id)


class AnswersView(LoginRequiredMixin, View):
    """
    This view is for input the answer based on generated answer
    """

    template_name = "autofill/answers.html"
    redirect_url = "autofill:detail-section"

    def get_false_questions(self, questions):
        for q in questions:
            try:
                correct = questions[q]["correct"]
            except KeyError as e:
                correct = "false"

            if correct == "false":
                return True

    def get(self, *args, **kwargs):
        section = Section.objects.get(pk=kwargs["pk"])

        try:
            questions = self.request.session[f"q {kwargs['pk']}"]
        except KeyError:
            questions = Question.objects.get_question_dict(section.id)
        
        if self.get_false_questions(questions):
            context = {
                "questions": questions
            }
            return render(self.request, self.template_name, context)

        else:
            messages.warning(self.request, "All answers has been answered. Regenerate question to re-answer")
            return redirect(self.redirect_url, kwargs["pk"])

    def post(self, *args, **kwargs):
        section = Section.objects.get(pk=kwargs["pk"])
        questions = self.request.session[f"q {kwargs['pk']}"]
        
        for q in questions:
            question_type = questions[q]["question_type"]

            question = Question.objects.add_question({
                "section": section,
                "text":q,
                "type":question_type,
                "choice_type":questions[q]["choice_type"],
                "correct":True
            })
            
            if question_type == "KisiPilihanGanda" or question_type == "PetakKotakCentang":
                row = questions[q]["answers"]["row"]
                for r in row:
                    text = self.request.POST.getlist(f"{q} {r}")

                    for t in text:
                        Answer.objects.add_answer({
                            "question": question,
                            "text": t,
                            "type": question_type,
                            "correct": True
                        })

            else:
                text = self.request.POST.getlist(q)
                
                for t in text:
                    Answer.objects.add_answer({
                        "question": question,
                        "text": t,
                        "type": question_type,
                        "correct": True
                    })

        try:
            del self.request.session[f"q {kwargs['pk']}"]
        except Exception as e:
            pass

        messages.success(self.request, "Successfuly save question and answer")
        return redirect(self.redirect_url, kwargs["pk"])
   

@login_required
def delete_section(request, pk):
    """ This view is for delete the selected section """

    section = Section.objects.get(pk=pk)
    if section:
        section.delete()

        try:
            del request.session[f"q {pk}"]
        
        except KeyError as e:
            pass
        
        messages.success(request, "Successfully delete form")
    else:
        messages.error(request, "Failed to delete Form")
    
    return redirect('autofill:dashboard')