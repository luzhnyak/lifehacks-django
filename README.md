# lifehacks-django
Lifehacks

## Створення віртуального середовища

```
python -m venv venv
venv\scripts\activate
```

## Команди для встановлення і зберігання залежностей:

`pip install -r requirements.txt`
`pip freeze > requirements.txt`

## Основні команди для розгортання проекту на Django:

`python -m pip install Django`
`django-admin startproject lifehacks .`

`python manage.py startapp main`
`python manage.py createsuperuser`
`python manage.py makemigrations`
`python manage.py migrate`