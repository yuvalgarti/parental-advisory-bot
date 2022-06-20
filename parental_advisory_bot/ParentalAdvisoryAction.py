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
        if tweet.entities and tweet.entities['media']:
            image = tweet.entities['media'][0]
            if image['media_url']:
                response = requests.get(image['media_url'])
                if response.status_code == 200:
                    with open(tweet.id_str + '.jpg', 'wb') as f:
                        f.write(response.content)
                        return True
        return False

    def paste_parental_advisory_on_image(self, path_to_image, is_border):
        original_image = Image.open(path_to_image)
        parental_advisory_image = Image.open('parental_advisory.png')

        original_height, original_width = original_image.size

        paste_height = int(original_height / 6)
        paste_width = int(original_width / 6)

        parental_advisory_image.thumbnail((paste_height, paste_width), Image.ANTIALIAS)

        paste_height = int(original_height - paste_height * 1.3)
        paste_width = int(original_width - paste_width)

        original_image.paste(parental_advisory_image, (paste_height, paste_width))

        if is_border:
            original_image = ImageOps.expand(original_image, border=5, fill='black')

        original_image.save(path_to_image, quality=95)

    def run(self, mention):
        comment = self.api.get_status(mention.in_reply_to_status_id)
        if self.save_tweet_image(comment):
            path_to_file = comment.id_str + '.jpg'
            is_border = "border" in mention.text.lower()
            self.paste_parental_advisory_on_image(path_to_file, is_border)
            status = '@' + mention.user.screen_name
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
