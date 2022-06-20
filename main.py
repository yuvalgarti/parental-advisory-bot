import logging
import os
import sys

import tweepy
from mention_bot import MentionHandler

from parental_advisory_bot.ParentalAdvisoryAction import ParentalAdvisoryAction
from parental_advisory_bot.firebase_service import FirebaseService

if __name__ == '__main__':

    firebase_config = {
        'apiKey': os.environ['PARENTAL_ADVISORY_FIREBASE_API_KEY'],
        'authDomain': os.environ['PARENTAL_ADVISORY_FIREBASE_AUTH_DOMAIN'],
        'databaseURL': os.environ['PARENTAL_ADVISORY_FIREBASE_DB_URL'],
        'storageBucket': os.environ['PARENTAL_ADVISORY_FIREBASE_STORAGE_BUCKET']
    }

    is_production = os.environ.get('IS_PRODUCTION', 'True') == 'True'

    auth = tweepy.OAuthHandler(os.environ['PARENTAL_ADVISORY_CONSUMER_KEY'], os.environ['PARENTAL_ADVISORY_CONSUMER_VALUE'])
    auth.set_access_token(os.environ['PARENTAL_ADVISORY_ACCESS_TOKEN_KEY'], os.environ['PARENTAL_ADVISORY_ACCESS_TOKEN_VALUE'])

    tweepy_api = tweepy.API(auth, wait_on_rate_limit=True)

    firebase_db = FirebaseService(firebase_config)

    log_modules = ['parental_advisory_bot', 'mention_bot']
    logFormat = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logFormat)

    for module_name in log_modules:
        logger = logging.getLogger(module_name)
        logger.setLevel('DEBUG')
        logger.addHandler(console_handler)

    parental_advisory_mention_action = ParentalAdvisoryAction(tweepy_api, is_production)
    mention_handler = MentionHandler(tweepy_api,
                                     parental_advisory_mention_action,
                                     firebase_db,
                                     is_production,
                                     int(os.environ.get('SCREENSHOT_TIMEOUT', 30)),
                                     int(os.environ.get('RETRY_COUNT', 3)))

    mention_handler.run()
