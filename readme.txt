# Script with CLI performing the following actions:
#   Uploading the weather forecast in database within inputted dates range [--upld dd.mm.yyyy dd.mm.yyyy]
#   Downloading the weather forecast from database within inputted dates range [--dwld dd.mm.yyyy dd.mm.yyyy]
#   Creation of cards with data downloaded in previous step [--card]
#   Show downloaded data on console [--show]
# At startup the script automatically downloaded the forecasts for previous week.

# The source of data is yandex.ru
# The postgres used as default database (database settings in database_initialization.py).

# To start script run: python main.py [command].

