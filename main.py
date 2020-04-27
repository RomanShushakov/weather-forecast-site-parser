# -*- coding: utf-8 -*-

import argparse

from weather_maker import DataBaseUpdater, QueryComposer, ForecastPresenter


def last_week_forecast():
    updater = DataBaseUpdater(start_date=None, end_date=None)
    updater.upload_forecast_to_db()
    updater.download_forecast_from_db()


def upload_forecast(start_date, end_date):
    updater = DataBaseUpdater(start_date=start_date, end_date=end_date)
    updater.upload_forecast_to_db()
    print(f'The weather forecast for dates in range {start_date} - {end_date} were \n'
          f'successfully uploaded from "yandex.com/weather/moscow" to database.')


def download_forecast(start_date, end_date):
    updater = DataBaseUpdater(start_date=start_date, end_date=end_date)
    updater.download_forecast_from_db()
    print(f'The dates range {start_date} - {end_date} was successfully saved in database.\n'
          f'This range will be used in further presentation of weather forecast.')


def show_forecast():
    composer = QueryComposer()
    presenter = ForecastPresenter(query=composer.query)
    presenter.show_forecast_on_console()


def create_cards_with_forecast():
    composer = QueryComposer()
    presenter = ForecastPresenter(query=composer.query)
    presenter.create_forecast_cards()


parser = argparse.ArgumentParser(
    description='Display the weather forecast in requested range of dates. '
                'Note: weather forecast is available only for current year.',
)
parser.add_argument('--upld',
                    metavar=('[range start date in format dd.mm.yyyy', 'range end date in format dd.mm.yyyy]'),
                    help='upload the forecast from yandex.com/weather/moscow to database for dates in range.',
                    required=False, nargs=2)
parser.add_argument('--dwld',
                    metavar=('[range start date in format dd.mm.yyyy', 'range end date in format dd.mm.yyyy]'),
                    help='download the forecast from database for dates in range.',
                    required=False, nargs=2)
parser.add_argument('--show', action='store_true',
                    help='show the forecast on console for last range of dates which was downloaded to database.',
                    required=False)
parser.add_argument('--card', action='store_true',
                    help='show the forecast on cards for last range of dates which was downloaded to database. '
                         'Enter "s" key to save shown card. The card will be saved in dd.mm.yyyy.png format. '
                         'Any other pressed key will close the shown card.',
                    required=False)

args = parser.parse_args()

if args.upld:
    start_date = args.upld[0]
    end_date = args.upld[1]
    upload_forecast(start_date=start_date, end_date=end_date)

if args.dwld:
    start_date = args.dwld[0]
    end_date = args.dwld[1]
    download_forecast(start_date=start_date, end_date=end_date)

if args.show:
    show_forecast()

if args.card:
    create_cards_with_forecast()

if not args.upld and not args.dwld and not args.show and not args.card:
    last_week_forecast()
    print(f'The weather forecast for last week was uploaded from "yandex.com/weather/moscow" to database.\n'
          f'For help input "-h" or "--help" after script name in command line.')
