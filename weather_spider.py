# -*- coding: utf-8 -*-

import os
import re
import datetime
import scrapy
from scrapy.crawler import CrawlerProcess


class WeatherSpider(scrapy.Spider):
    name = 'weather_spider'
    start_urls = [
        'https://yandex.ru/pogoda/moscow/month?via=ms',
    ]
    base_url = 'https://yandex.ru'

    def __init__(self, name=None, **kwargs):
        super().__init__(name=None, **kwargs)
        self.day_pattern = kwargs['patterns']['day']
        self.month_pattern = kwargs['patterns']['month']
        self.month_numbers = kwargs['patterns']['month_numbers']
        self.weather_transform = kwargs['patterns']['weather_transform']
        self.start_date = kwargs['dates_range']['start_date']
        self.end_date = kwargs['dates_range']['end_date']

    def parse(self, response):
        links_raw = response.xpath('/html/body/div/div[5]/section[1]/div[1]/div[1]/div[1]/div[2]/*/label').xpath(
            './/*[@href]')
        links = [link.attrib['href'] for link in links_raw if link.attrib['href']]
        months = response.xpath('/html/body/div/div[5]/section[1]/div[1]/div[1]/div[1]/div[2]/*/label').xpath(
            './/*/text()').getall()
        for link, month in zip(links, months):
            if not re.search(self.month_pattern, month.lower()):
                continue
            current_month_number = self.month_numbers[re.search(self.month_pattern, month.lower())[0]][0]
            if current_month_number in range(self.start_date.month, self.end_date.month + 1):
                new_url = self.base_url + link
                yield scrapy.Request(new_url, callback=self.parse_temp, cb_kwargs=dict(link=link, month=month))

    def parse_temp(self, response, link, month):
        cells = response.xpath('//*/div[contains(@class, "day__detailed-container-center")]')
        dates = [cell.xpath('.//h6/text()').get() for cell in cells]
        temps = [cell.xpath('.//*[contains(@class, "detailed-basic-temp")]').xpath(
            './/*[@class="temp__value"]/text()').getall() for cell in cells]
        images = [cell.xpath('.//div/img').attrib['src'] for cell in cells]
        for date, temp, image in zip(dates, temps, images):
            weather_picture = image[image.rfind('/'):]
            if weather_picture in self.weather_transform:
                weather = self.weather_transform[weather_picture]
            else:
                weather = weather_picture
            found_day = re.search(self.day_pattern, date.lower())
            found_month = re.search(self.month_pattern, date.lower())
            if found_day and found_month:
                transformed_date = datetime.date(
                    day=int(found_day[0]),
                    month=self.month_numbers[found_month[0]][0],
                    year=self.month_numbers[found_month[0]][1]
                )
                if self.start_date <= transformed_date <= self.end_date:
                    yield {
                        'weather': weather, 'day_temp': temp[0], 'night_temp': temp[1],
                        'date': transformed_date, 'web_date': date, 'image': image,
                        'month_page': month, 'link': link
                    }


def crawl_web_site(output_file, **kwargs):
    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        # 'FEED_URI': output_file,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DOWNLOAD_DELAY': 1.5,
        'ITEM_PIPELINES': {
            'pipelines.WeatherMakerPipeline': 300,
        },
        'LOG_LEVEL': 'ERROR'
        # 'LOG_ENABLED': False
    })
    process.crawl(WeatherSpider, patterns=kwargs['patterns'], dates_range=kwargs['dates_range'])
    process.start()


if __name__ == '__main__':
    year = datetime.date.today().year
    re_month = re.compile(r'янв|фев|мар|апр|май|мая|июн|июл|авг|сен|окт|ноя|дек')
    re_day = re.compile(r'\d{,2}')
    month_numbers = {
        'янв': (1, year), 'фев': (2, year), 'мар': (3, year), 'апр': (4, year), 'май': (5, year), 'мая': (5, year),
        'июн': (6, year), 'июл': (7, year), 'авг': (8, year), 'сен': (9, year), 'окт': (10, year), 'ноя': (11, year),
        'дек': (12, year)
    }
    weather_transform = {
        '/bkn_-ra_d.svg': 'partly cloudy/light rain showers',
        '/bkn_d.svg': 'partly cloudy',
        '/bkn_ra_d.svg': 'partly cloudy/light rain showers',
        '/ovc.svg': 'cloudy',
        '/ovc_-ra.svg': 'rain showers',
        '/ovc_ra.svg': 'rain showers',
        '/ovc_ra_sn.svg': 'rain showers/snow showers',
        '/ovc_sn.svg': 'snow showers',
        '/skc_d.svg': 'fair'
    }
    patterns = {
        'day': re_day, 'month': re_month, 'month_numbers': month_numbers,
        'weather_transform': weather_transform
    }
    dates_range = {
        'start_date': datetime.date(year=2020, month=1, day=1),
        'end_date': datetime.date(year=2020, month=2, day=22)
    }
    output_file = 'weather_out_example.json'
    path = os.path.normpath(os.path.dirname(__file__))
    if output_file in os.listdir(path):
        os.remove(os.path.join(path, output_file))

    process = CrawlerProcess(settings={
        'FEED_FORMAT': 'json',
        # 'FEED_URI': output_file,
        'FEED_EXPORT_ENCODING': 'utf-8',
        'DOWNLOAD_DELAY': 1.5,
        'ITEM_PIPELINES': {
           'pipelines.WeatherMakerPipeline': 300,
        },
        # 'LOG_ENABLED': False
    })
    process.crawl(WeatherSpider, patterns=patterns, dates_range=dates_range)
    process.start()
