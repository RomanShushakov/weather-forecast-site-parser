# -*- coding: utf-8 -*-

import peewee

db_name = 'weather_forecast'
user = 'weather'
password = 'forecast'
# database = peewee.PostgresqlDatabase(db_name, user=user, password=password)
weather_url = f'postgresql://{user}:{password}@localhost:5432/{db_name}'
