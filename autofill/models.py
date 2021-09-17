from django.db import models
from django.shortcuts import reverse
from django.conf import settings

from . managers import (
    SectionManager, LogManager,
    QuestionManager, AnswerManager
)

# django signals
from django.db.models.signals import post_delete
from django.dispatch import receiver

from django.utils.translation import ugettext_lazy as _

# django celery beat
from django_celery_beat.models import PeriodicTask


SCHEDULE_TYPE_CHOICES = (
        ('Interval', 'Interval'),
        ('Clocked', 'Clocked'),
        ('Crontab', 'Crontab'),
        ('Solar', 'Solar')
)


class Section(models.Model):

    SECTION_STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Disabled', 'Disabled')
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    url = models.URLField()

    schedule_type = models.CharField(choices=SCHEDULE_TYPE_CHOICES, max_length=20, blank=True, null=True)

    task = models.OneToOneField(PeriodicTask, on_delete=models.SET_NULL, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = SectionManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('autofill:detail-section', kwargs={
            'pk': self.pk,
        })


'''
Delete the Periodic Task field that related to the Section models
And also delete the Interval/Crontab/Solar/Clocked field
that related to the Periodic Task models
'''
@receiver(post_delete, sender=Section)
def delete_periodic_task(sender, instance, **kwargs):
    try:
        instance.task.delete()
    except Exception:
        pass

@receiver(post_delete, sender=PeriodicTask)
def delete_schedule(sender, instance, **kwargs):
    if instance.interval:
        instance.interval.delete()
    elif instance.clocked:
        instance.clocked.delete()
    elif instance.crontab:
        instance.crontab.delete()
    elif instance.solar:
        instance.solar.delete()
    

QUESTION_TYPE = (
        ('JawabanSingkat', 'Jawaban Singkat Display'),
        ('Paragraf', 'Paragraf'),
        ('PilihanGanda', 'Pilihan Ganda'),
        ('KotakCentang', 'Kotak Centang'),
        ('DropDown', 'DropDown'),
        ('SkalaLinier', 'Skala Linier'),
        ('KisiPilihan Ganda', 'Kisi Pilihan Ganda'),
        ('PetakKotak Centang', 'Petak Kotak Centang'),
        ('Tanggal', 'Tanggal'),
        ('Waktu', 'Waktu')
)

CHOICE_TYPE = (
    ('SingleElement', 'Single Element'),
    ('MultipleElement', 'Multiple Element')
)


class Question(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    type = models.CharField(choices=QUESTION_TYPE, max_length=100, blank=True, null=True)
    choice_type = models.CharField(choices=CHOICE_TYPE, max_length=100, blank=True, null=True)
    
    correct = models.BooleanField(default=False)

    slug = models.SlugField()

    objects = QuestionManager()

    def __str__(self):
        return self.text


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    correct = models.BooleanField(default=False)
    type = models.CharField(choices=QUESTION_TYPE, max_length=100)

    objects = AnswerManager()

    def __str__(self):
        return self.text


class Log(models.Model):

    STATUS_CHOICES = (
        ('Success', 'Success'),
        ('Failed', 'Failed')
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=100)
    message = models.TextField(blank=True, null=True)

    objects = LogManager()
    
    def __str__(self):
        return self.user.email