from django.db import models

# This app intentionally does not define any Django ORM models.
# All real estate data is read directly from an Excel file
# (realestate/data/sample_data.xlsx) into a pandas DataFrame at server
# startup, which avoids the need for a database migration workflow for
# this read-only dataset.
#
# If you want to persist data or enable admin CRUD, define your models here
# and run: python manage.py makemigrations && python manage.py migrate
