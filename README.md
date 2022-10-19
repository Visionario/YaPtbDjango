YaPtbDjango 
------------   
### Yet another Python Telegram Bot with Django      

A very simple integration between [Django](https://www.djangoproject.com/) and [Python Telegram Bot](https://github.com/python-telegram-bot/python-telegram-bot), ready to use.

Version: 0.1.0

Supported:   
* Python: 3.7+   
* Django: 4.x (maybe 3.x)   
* Python Telegram Bot: 13   

------------


Quickstart (polling mode)
------------   

* Clone this repository   
* Copy *settings_dev.py.sample* on *settings_dev.py*   
* Check and edit/change TELEGRAM BOT TOKEN on settings using your token from [@BotFather](https://t.me/BotFather).   
* Add your telegram "user_id" on 'SUPERADMINS' (settings file)    
* Create virtual environment   
  * `python3 -m venv venv`
* Install requirements   
  * `pip install -r requirements.txt`   
* Make migrations   
  * `python manage.py makemigrations`     
  * `python manage.py migrate`   
  * `python manage.py createsuperuser`   
* Start Django:  
  * `python manage.py runserver`   

* Start BOT (another console):   
  * `YAPTBDJANGO_BOT=OK python manage.py botpolling --token="TELEGRAM BOT TOKEN"`

-----------



# Contribution Guidelines

Contributions are welcome!   

----------


Credits
---------

Inspired and some lines of code...:
https://github.com/JungDev/django-telegrambot

Some reference...:
https://github.com/CarlosLugones/ptb-django-cookiecutter

Take a look...:
https://github.com/ohld/django-telegram-bot



--------

Live Long And Prosper - L.L.A.P 🖖