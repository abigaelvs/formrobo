from celery.decorators import task

from .utils import submit_form

@task(name='send_form_task')
def send_form_task(id):
    """ Create a celery task to submit the form """
    submit_form(id)
