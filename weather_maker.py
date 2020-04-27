# -*- coding: utf-8 -*-


import re
import os
import cv2
import datetime
import peewee
from playhouse.db_url import connect

from weather_spider import crawl_web_site
from database_initialization import weather_url as url


class DatabaseConnector:

    def __init__(self, url):
        database_proxy = peewee.DatabaseProxy()

        class BaseTable(peewee.Model):
            class Meta:
                database = database_proxy

        class WeatherForecast(BaseTable):
            weather = peewee.CharField()
            day_temp = peewee.CharField()
            night_temp = peewee.CharField()
            date = peewee.DateField()
            image = peewee.CharField()

        class DatesRequests(BaseTable):
            request_start_date = peewee.DateField()
            request_end_date = peewee.DateField()

        database = connect(url)
        database_proxy.initialize(database)
        if not database.table_exists('WeatherForecast'.lower()) or not database.table_exists('DatesRequests'.lower()):
            database.create_tables([WeatherForecast, DatesRequests])
        self.WeatherForecast = WeatherForecast
        self.DatesRequests = DatesRequests


class DataBaseUpdater:

    def __init__(self, start_date, end_date):
        db_conn = DatabaseConnector(url=url)
        self.request_table = db_conn.DatesRequests

        self.start_date = (datetime.date.today() - datetime.timedelta(days=7)) if not start_date else self._date_strp(
            date=start_date)
        self.end_date = datetime.date.today() if not end_date else self._date_strp(date=end_date)
        self.year = datetime.date.today().year
        self.re_day = re.compile(r'\d{,2}')
        self.re_month = re.compile(r'янв|фев|мар|апр|май|мая|июн|июл|авг|сен|окт|ноя|дек')
        self.month_numbers = {
            'янв': (1, self.year), 'фев': (2, self.year), 'мар': (3, self.year), 'апр': (4, self.year),
            'май': (5, self.year), 'мая': (5, self.year), 'июн': (6, self.year), 'июл': (7, self.year),
            'авг': (8, self.year), 'сен': (9, self.year), 'окт': (10, self.year), 'ноя': (11, self.year),
            'дек': (12, self.year)
        }
        self.weather_transform = {
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
        self.patterns = {
            'day': self.re_day, 'month': self.re_month, 'month_numbers': self.month_numbers,
            'weather_transform': self.weather_transform
        }
        self.dates_range = {
            'start_date': self.start_date,
            'end_date': self.end_date
        }
        self.forecast_file = datetime.date.today().strftime('%d.%m.%y_%H.%M_weather.json')

    def _date_correctness_check(self, date):
        re_date = re.compile(r'^\d{2}\.\d{2}\.\d{4}$')
        if not re.match(re_date, date) or int(date[-4:]) != datetime.date.today().year:
            raise BaseException(f'not correct date {date} was inputted!')
        return True

    def _date_strp(self, date):
        if self._date_correctness_check(date=date):
            stripped_date = datetime.datetime.strptime(date, "%d.%m.%Y")
            return datetime.date(year=stripped_date.year, month=stripped_date.month, day=stripped_date.day)

    def upload_forecast_to_db(self):
        crawl_web_site(output_file=self.forecast_file, patterns=self.patterns, dates_range=self.dates_range)

    def download_forecast_from_db(self):
        new_day_forecast = self.request_table(request_start_date=self.start_date, request_end_date=self.end_date)
        new_day_forecast.save()


class QueryComposer:

    def __init__(self):
        db_conn = DatabaseConnector(url=url)
        self.request_table = db_conn.DatesRequests
        self.weather_table = db_conn.WeatherForecast

        self.request_start_date = self.request_table.select().order_by(
            self.request_table.id.desc()).get().request_start_date
        self.request_end_date = self.request_table.select().order_by(
            self.request_table.id.desc()).get().request_end_date

        self.query = self._query_existense_check()

    def _query_existense_check(self):
        query = (self.weather_table
                 .select()
                 .where(self.request_start_date <= self.weather_table.date,
                        self.weather_table.date <= self.request_end_date)
                 .order_by(self.weather_table.date, self.weather_table.id.desc())
                 .limit()
                 .distinct(self.weather_table.date))
        if not query:
            raise BaseException(f'No data in database for requested dates range {self.request_start_date} - '
                                f'{self.request_end_date}.\n'
                                f'Please, upload data to database firstly.')
        return query


class ForecastPresenter:

    def __init__(self, query):
        self.query = query
        self.background_color = {
            'ovc.svg.png': [128, 128, 128], 'bkn_d.svg.png': [128, 128, 128],
            'bkn_ra_d.svg.png': [255, 0, 0], 'bkn_-ra_d.svg.png': [255, 0, 0],
            'ovc_ra.svg.png': [255, 0, 0], 'ovc_-ra.svg.png': [255, 0, 0],
            'ovc_ra_sn.svg.png': [255, 153, 51], 'ovc_sn.svg.png': [255, 153, 51],
            'skc_d.svg.png': [0, 255, 255]
        }
        self.path = os.path.normpath(os.path.dirname(__file__))
        self.pictures_path = os.path.normpath(os.path.join(self.path, 'weather_pictures'))
        self.card_template = os.path.normpath(os.path.join(self.pictures_path, 'card_template.jpg'))

    def show_forecast_on_console(self):
        for i, weather in enumerate(self.query):
            print(f'{i + 1}. Date: {weather.date.strftime("%d-%m-%Y")}, '
                  f'weather: {weather.weather}, '
                  f'day temp: {weather.day_temp}, '
                  f'night temp: {weather.night_temp}')

    def create_forecast_cards(self):
        for weather in self.query:
            white = [255, 255, 255]
            image = weather.image
            date_text = f'Date: {weather.date.strftime("%d-%m-%Y")}'
            weather_text = f'{weather.weather}'
            day_temp_text = f'Day temp: {weather.day_temp.replace("−", "-")}'
            night_temp_text = f'Night temp: {weather.night_temp.replace("−", "-")}'
            card_color = self.background_color[image[image.rfind('/') + 1:] + '.png']
            icon_image_path = os.path.normpath(
                os.path.join(self.pictures_path, image[image.rfind('/') + 1:] + '.png'))
            background_image = cv2.imread(self.card_template)
            card_height, card_width = background_image.shape[: 2]
            for i in range(card_width):
                for j in range(card_height):
                    b = linear_interpolation(init_val=card_color[0], final_val=white[0], range=card_width, pos=i)
                    g = linear_interpolation(init_val=card_color[1], final_val=white[1], range=card_width, pos=i)
                    r = linear_interpolation(init_val=card_color[2], final_val=white[2], range=card_width, pos=i)
                    background_image[j, i] = [b, g, r]
            icon_image = cv2.imread(icon_image_path)
            shrinked_icon_image = cv2.resize(icon_image, (150, 150))
            rows_shrink, cols_shrink = 150, 150
            roi = background_image[0:rows_shrink, card_width - rows_shrink:card_width]
            icon2gray = cv2.cvtColor(shrinked_icon_image, cv2.COLOR_BGR2GRAY)
            ret, mask = cv2.threshold(icon2gray, 220, 255, cv2.THRESH_BINARY_INV)
            mask_inv = cv2.bitwise_not(mask)
            background_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)
            icon_fg = cv2.bitwise_and(shrinked_icon_image, shrinked_icon_image, mask=mask)
            dst = cv2.add(background_bg, icon_fg)
            background_image[0:rows_shrink, card_width - rows_shrink:card_width] = dst
            cv2.putText(img=background_image, text=date_text, org=(20, 50),
                        fontFace=2, fontScale=0.7, color=(0, 0, 0))
            cv2.putText(img=background_image, text=weather_text, org=(20, 210),
                        fontFace=2, fontScale=0.7, color=(0, 0, 0))
            cv2.putText(img=background_image, text=day_temp_text, org=(20, 105),
                        fontFace=2, fontScale=0.7, color=(0, 0, 0))
            cv2.putText(img=background_image, text=night_temp_text, org=(20, 160),
                        fontFace=2, fontScale=0.7, color=(0, 0, 0))
            cv2.imshow(f'{weather.date.strftime("%d-%m-%Y")}', background_image)
            key = cv2.waitKey(0)
            if key == ord("s"):
                card_name = f'{weather.date.strftime("%d-%m-%Y")}.png'
                cards_folder_name = 'cards'
                cards_folder = os.path.normpath(os.path.join(self.path, cards_folder_name))
                if cards_folder_name not in os.listdir(self.path):
                    os.makedirs(cards_folder)
                if card_name in cards_folder:
                    os.remove(os.path.normpath(os.path.join(cards_folder, card_name)))
                card_path = os.path.normpath(os.path.join(cards_folder, card_name))
                cv2.imwrite(card_path, background_image)
            cv2.destroyAllWindows()


def linear_interpolation(init_val, final_val, range, pos):
    return init_val + (final_val - init_val) / range * pos


if __name__ == '__main__':
    start_date = None
    end_date = None
    updater = DataBaseUpdater(start_date=start_date, end_date=end_date)
    updater.upload_forecast_to_db()
    updater.download_forecast_from_db()
    composer = QueryComposer()
    presenter = ForecastPresenter(query=composer.query)
    presenter.show_forecast_on_console()
    presenter.create_forecast_cards()
