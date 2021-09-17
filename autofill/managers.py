from django.db import models

from django.utils.text import slugify

# django celery beat
from django_celery_beat.models import PeriodicTask, IntervalSchedule, ClockedSchedule, CrontabSchedule, SolarSchedule


class SectionManager(models.Manager):

    def get_section_by_user(self, user: str):
        sections = self.filter(user=user).order_by("-date_created")
        return sections

    def get_section_by_name(self, name: str):
        sections = self.filter(name=name)
        return sections

    def get_enabled_section(self, user):
        sections = self.get_section_by_user(user).filter(task__enabled=True).count()
        return sections
    
    def get_disabled_section(self, user):
        sections = self.get_section_by_user(user).filter(task__enabled=True).count()
        return sections

    def get_questions(self):
        return self.question_set.all()
    
    def get_number_of_questions(self):
        return self.question_set.all().count()

    def add_section(self, name, url, user):
        try:
            section = self.create(
                user=user,
                name=name,
                url=url,
            )
            section.save()

            return section
        except Exception as e:
            return e

    def update_section(self, section_id, name):
        section = self.get(pk=int(section_id))

        try:
            section.name = name
            section.save()

            try:
                periodic_task = PeriodicTask.objects.get(pk=section.task.id)

                periodic_task.name = f"{section.user.email} {name} Task"
                periodic_task.save()
            except Exception as e:
                pass
            
            return section

        except Exception as e:
            return e

    # ==== Scheduling manager ====
    
    def add_task(self, section, periodic_task: PeriodicTask, schedule_type: str):
        try:
            section.task = periodic_task
            section.schedule_type = schedule_type
            section.save()

        except Exception as e:
            return e

    def add_interval_task(self, data):
        try:
            periodic_task = PeriodicTask(
                name=data["name"],
                task='send_form_task',
                interval=data["interval"],
                start_time=(data["start_time"] if data["start_time"] else None),
                one_off=data["one_off"],
                args=data["args"],
                enabled=False
            )
            periodic_task.save()
            
            return periodic_task

        except Exception as e:
            return e

    def add_clocked_task(self, data):
        try:
            periodic_task = PeriodicTask(
                name=data["name"],
                task='send_form_task',
                clocked=data["clocked"],
                start_time=(data["start_time"] if data["start_time"] else None),
                one_off=True,
                args=data["args"],
                enabled=False
            )
            periodic_task.save()
            
            return periodic_task

        except Exception as e:
            return e

    def add_crontab_task(self, data):
        try:
            periodic_task = PeriodicTask(
                name=data["name"],
                task='send_form_task',
                crontab=data["crontab"],
                start_time=(data["start_time"] if data["start_time"] else None),
                one_off=data["one_off"],
                args=data["args"],
                enabled=False
            )
            periodic_task.save()
            
            return periodic_task

        except Exception as e:
            return e

    def add_solar_task(self, data):
        try:
            periodic_task = PeriodicTask(
                name=data["name"],
                task='send_form_task',
                solar=data["solar"],
                start_time=(data["start_time"] if data["start_time"] else None),
                one_off=data["one_off"],
                args=data["args"],
                enabled=False
            )
            periodic_task.save()
            
            return periodic_task

        except Exception as e:
            return e

    def add_periodic_task(self, data):
        switcher = {
            "Interval": self.add_interval_task(data),
            "Clocked": self.add_clocked_task(data),
            "Crontab": self.add_crontab_task(data),
            "Solar": self.add_solar_task(data)
        }

        return switcher.get(data["schedule_type"])

    def add_interval(self, every, period):
        try:
            interval = IntervalSchedule(
                every=every,
                period=period
            )
            interval.save()

            return interval

        except Exception as e:
            return e

    def add_clocked(self, clocked_time):
        try:
            clocked = ClockedSchedule(
                clocked_time=clocked_time
            )
            clocked.save()
            return clocked
        except  Exception as e:
            return e

    def add_crontab(self, data):
        try:
            crontab = CrontabSchedule(
                minute=data["minute"],
                hour=data["hour"],
                day_of_week=data["day_of_week"],
                day_of_month=data["day_of_month"],
                month_of_year=data["month_of_year"],
                timezone=data["timezone"]
            )
            crontab.save()
            return crontab
        except Exception as e:
            return e

    def add_solar(self, data):
        try:
            solar = SolarSchedule(
                latitude=data["latitude"],
                longitude=data["longitude"],
                event=data["event"]
            )
            solar.save()
            return solar
        except Exception as e:
            return e


class QuestionManager(models.Manager):

    def get_question_by_section(self, section_id: int):
        questions = self.filter(section__id=int(section_id))
        return questions

    def get_question_dict(self, section_id: int):
        """Get all questions and answers and convert to dictionary"""

        questions_qs = self.get_question_by_section(section_id)
        questions = {}
        for q in questions_qs:
            questions[q.text] = {"question_type": q.type, "choice_type": q.choice_type, "answers": []}
            if q.correct:
                questions[q.text]["correct"] = "true"
            else:
                questions[q.text]["correct"] = "false"

            answers_qs = q.answer_set.all()
            for a in answers_qs:
                questions[q.text]["answers"].append(a.text)
        return questions

    def get_answers(self):
        return self.answer_set.all()

    def add_question(self, data):
        try:
            question = self.create(
                section=data["section"],
                text=data["text"],
                type=data["type"],
                choice_type=data["choice_type"],
                correct=data["correct"],
            )
            question.save()

            return question

        except Exception as e:
            return e

    def save(self, *args, **kwargs):
        self.slug = slugify(self.text)
        super(self).save(*args, **kwargs)


class AnswerManager(models.Manager):
    def get_answer_by_question(self, question: str):
        return self.filter(question=question)

    def add_answer(self, data):
        try:
            answer = self.create(
                question=data["question"],
                text=data["text"],
                type=data["type"],
                correct=data["correct"]
            )
            answer.save()

            return answer

        except Exception as e:
            return e


class LogManager(models.Manager):

    def get_log_by_user(self, user: str):
        logs = self.filter(user=user).order_by("-date")
        return logs

    def get_log_by_section(self, section):
        logs = self.filter(section=section)
        return logs

    def get_successfuly_submitted_section(self, section):
        return self.filter(section=section, status="Success")

    def get_failed_submitted_section(self, section):
        return self.filter(section=section, status="Failed")

    def get_submitted_form(self, user: str):
        return self.get_log_by_user(user).count()

    def get_successfuly_submitted(self, user: str):
        logs = self.get_log_by_user(user).filter(status="Success").count()
        return logs
    
    def get_failed_to_submit(self, user: str):
        logs = self.get_log_by_user(user).filter(status="Failed").count()
        return logs

    def add_log(self, data):
        try:
            log = self.create(
                user=data["user"],
                section=data["section"],
                status=data["status"],
                message=data["message"]
            )
            log.save()

            return log
        except Exception as e:
            return e
    