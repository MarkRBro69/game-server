#!/bin/sh

python manage.py makemigrations --no-input
python manage.py migrate --no-input
python manage.py runserver 0.0.0.0:8002