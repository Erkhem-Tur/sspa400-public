# -*- coding: utf-8 -*-
import os, django, sys
sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from lms.models import Department
Department.objects.get_or_create(name='Хамгаалалтын 6-р хэлтэс', defaults={'order': 1})
Department.objects.get_or_create(name='Төрийн Ордны хамгаалалтын хэлтэс', defaults={'order': 2})
print('Departments created successfully')
