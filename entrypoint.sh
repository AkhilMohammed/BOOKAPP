#! /bin/bash

while !</dev/tcp/db/5432; do
    sleep 20
done


python manage.py makemigrations
python manage.py makemigrations rest_framework_simplejwt --empty
python manage.py migrate 
python manage.py runserver 0.0.0.0:8080
gunicorn celery_demo.wsgi:application -b 0.0.0.0:8080
