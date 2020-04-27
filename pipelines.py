# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import peewee

from database_initialization import weather_url as url
from weather_maker import DatabaseConnector


class WeatherMakerPipeline(object):

    def __init__(self):
        db_conn = DatabaseConnector(url=url)
        self.weather_table = db_conn.WeatherForecast

    def process_item(self, item, spider):
        new_day_forecast = self.weather_table(weather=item['weather'], day_temp=item['day_temp'],
                                              night_temp=item['night_temp'], date=item['date'],
                                              image=item['image'])
        new_day_forecast.save()
        return item
