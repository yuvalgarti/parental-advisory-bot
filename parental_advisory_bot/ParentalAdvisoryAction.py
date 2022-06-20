import os

import requests
from PIL import Image, ImageOps
from mention_bot import MentionAction
import logging


class ParentalAdvisoryAction(MentionAction):
    def __init__(self, api, is_production):
        self.api = api
        self.is_production = is_production
        self.logger = logging.getLogger(__name__)

    def save_tweet_image(self, tweet):
        if 'media' in tweet.entities:
            image = tweet.entities['media'][0]
            if image['media_url']:
                response = requests.get(image['media_url'])
                if response.status_code == 200:
                    with open(tweet.id_str + '.jpg', 'wb') as f:
                        f.write(response.content)
                        return True
        return False

    def paste_parental_advisory_on_image(self, path_to_image, is_border=False):
        original_image = Image.open(path_to_image)
        parental_advisory_image = Image.open('parental_advisory.png')

        original_height, original_width = original_image.size

        parental_advisory_image_thumbnail_size = max(int(original_height / 6), int(original_width / 6))

        parental_advisory_image.thumbnail((parental_advisory_image_thumbnail_size, parental_advisory_image_thumbnail_size),
                                          Image.ANTIALIAS)
        parental_advisory_image_height, parental_advisory_image_width = parental_advisory_image.size

        move_factor = 1.3
        paste_height = int(original_height - parental_advisory_image_height * move_factor)
        paste_width = int(original_width - parental_advisory_image_width * move_factor)

        original_image.paste(parental_advisory_image, (paste_height, paste_width))

        if is_border:
            original_image = ImageOps.expand(original_image, border=5, fill='black')

        original_image.save(path_to_image, quality=95)

    def run(self, mention):
        comment = self.api.get_status(mention.in_reply_to_status_id)
        status = '@' + mention.user.screen_name
        if self.save_tweet_image(comment):
            path_to_file = comment.id_str + '.jpg'
            is_border = "border" in mention.text.lower()
            self.paste_parental_advisory_on_image(path_to_file, is_border)
            if self.is_production:
                media = self.api.media_upload(path_to_file)
                try:
                    self.api.update_status(status=status, in_reply_to_status_id=mention.id,
                                           media_ids=[media.media_id])
                    pass
                finally:
                    if os.path.exists(path_to_file):
                        self.logger.debug('removing media file')
                        # os.remove(path_to_file)
            else:
                self.logger.info('TESTING MODE - path_to_file: {}, status: {}, in_reply_to_status_id: {}, '
                                 .format(path_to_file, status, mention.id))
        else:
            status = status + ' There is no media in this tweet :('
            if self.is_production:
                self.api.update_status(status=status, in_reply_to_status_id=mention.id)
            else:
                self.logger.info('TESTING MODE - status: {}, in_reply_to_status_id: {}, '
                                 .format(status, mention.id))
