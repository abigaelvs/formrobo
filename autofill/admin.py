from django.contrib import admin
from .models import Section, Question, Answer, Log


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    readonly_fields = ['date_created']

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    readonly_fields = ['date']

class AnswerInline(admin.TabularInline):
    model = Answer

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = [
        'text',
        'type',
        'correct',
        'question'
    ]
    list_filter = [
        'question',
        'correct'
    ]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = [
        'text',
        'section',
        'type'
    ]

    list_filter = [
        'section',
        'type'
    ]
    inlines = [AnswerInline]


