# Form Robo
A project to automate your google form process


## How to use
- Clone/download this repository
- Install Rabbitmq (https://www.rabbitmq.com/download.html)
- Install all the requirements with 
```
pip install -r requirements.txt
```
- Run web server with 
```
python manage.py runserver
```
- Run Celery with 
```
celery -A automation worker --loglevel=info
```
- Run Celery beat with
```
celery -A automation beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
- Open http://localhost:8000/ in your browser
- Add New Form and input the google form link
- Set the schedule
- Activate auto submit


## Library Used
- BeautifulSoup4 https://www.crummy.com/software/BeautifulSoup/
- Selenium Webdriver https://www.selenium.dev/
- Celery https://docs.celeryproject.org/en/stable/
