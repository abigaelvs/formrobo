from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.expressions import Value
from django.http.request import validate_host
from django.utils.text import slugify
from django.shortcuts import reverse
from django.conf import settings

# django signals
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from django.utils.translation import ugettext_lazy as _


# django celery beat
from django_celery_beat.models import PeriodicTask

import json

from django.utils import timezone


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

    def __str__(self):
        return self.name

    def get_questions(self):
        return self.question_set.all()
    
    def get_number_of_questions(self):
        return self.question_set.all().count()

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
    


TYPE_CHOICES = (
        ('Jawaban Singkat', 'Jawaban Singkat'),
        ('Paragraf', 'Paragraf'),
        ('Pilihan Ganda', 'Pilihan Ganda'),
        ('Kotak Centang', 'Kotak Centang'),
        ('Drop Down', 'Drop Down'),
        ('Skala Linier', 'Skala Linier'),
        ('Kisi Pilihan Ganda', 'Kisi Pilihan Ganda'),
        ('Petak Kotak Centang', 'Petak Kotak Centang'),
        ('Tanggal', 'Tanggal'),
        ('Waktu', 'Waktu')
)


class Question(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    type = models.CharField(choices=TYPE_CHOICES, max_length=100)
    correct = models.BooleanField(default=False)

    slug = models.SlugField()

    def __str__(self):
        return self.text

    def get_answers(self):
        return self.answer_set.all()

    def save(self, *args, **kwargs):
        self.slug = slugify(self.text)
        super(Question, self).save(*args, **kwargs)
        
    def get_row(self):
        kisi_pilihan_ganda = self.objects.filter(question=question, type='Kisi Pilihan Ganda')
        return self.kisi_pilihan_ganda.split(',')

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=100)
    type = models.CharField(choices=TYPE_CHOICES, max_length=100)
    correct = models.BooleanField(default=False)

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
    
    def __str__(self):
        return self.user.username