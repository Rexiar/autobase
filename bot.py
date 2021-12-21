import tweepy
import config
import time
import requests
from requests_oauthlib import OAuth1
import re
from PIL import Image, ImageDraw, ImageFont


class bot:
    def __init__(self):
        self.auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        self.auth.set_access_token(config.access_token, config.access_token_secret)
        self.api = tweepy.API(self.auth)
        self.trigger = config.trigger
        self.trigger2 = config.trigger_text_to_pic
    
    def send_error(self, sender_id = None, x = None):
        self.api.send_direct_message(recipient_id = sender_id, text='[BOT] ERROR')
        print(x)

    def read_dm(self):
        dmslist = list()
        try:
            self.dms = self.api.get_direct_messages()
            for x in range(len(self.dms)):
                message = self.dms[x].message_create['message_data']['text']
                id = self.dms[x].id
                if self.trigger in message.lower() or self.trigger2 in message.lower():
                    sender_id = self.dms[x].message_create['sender_id']
                    if 'attachment' not in self.dms[x].message_create['message_data']:
                        if len(self.dms[x].message_create['message_data']['entities']['urls'])>0:
                            print(message)
                            dmslist.append(dict(message = message, sender_id = sender_id, id = id, link = self.dms[x].message_create['message_data']['entities']['urls'][0]['expanded_url'], media = None, media_url = None, type = "link"))
                        else:
                            print(message)
                            dmslist.append(dict(message = message, sender_id = sender_id, id = id,  media = None, media_url = None, type = None))
                            dmslist.reverse()
                    else:
                        if self.trigger2 not in message.lower():
                            print(message)
                            dmslist.append(dict(message = message, sender_id = sender_id, id = id,  media = None, link = None, media_url = self.dms[x].message_create['message_data']['attachment']['media']['media_url'], type = self.dms[x].message_create['message_data']['attachment']['media']['type']))
                            dmslist.reverse()
                        else:
                            self.send_error(sender_id = sender_id, x = "[BOT] ERROR")
                            pass
        except Exception as x:
            print(x)
            time.sleep(60)
            pass
        return dmslist

    def post_tweet(self, text = None, sender_id = None):
        if len(text) > 280:
            tweet1 = 0
            while len(text) >280:
                first = 0
                last = 272
                very_last = len(text)
                split = text[260:last].split(' ')
                tweet = text[first:last-len(split[-1])] + '(cont..)'
                if tweet1 == 0:
                    try:
                        first_tweet = self.api.update_status(tweet)
                        tweet1 = first_tweet.id
                        try:
                            self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet1))
                        except Exception as x:
                            print(x)
                            pass
                    except Exception as x:
                        self.send_error(sender_id = sender_id, x = x)
                        pass
                else:
                    try:
                        reply_tweet = self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
                        tweet1 = reply_tweet.id
                        time.sleep(2)
                    except Exception as x:
                        self.send_error(sender_id = sender_id, x = x)
                        pass
                text = text[last-len(split[-1]):very_last]
                tweet = text[first:last-len(split[-1])]
                time.sleep(2)
            self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
        else:
            try:
                tweet = self.api.update_status(text)
                try:
                    self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet.id))
                except Exception as x:
                    print(x)
                    pass
            except Exception as x:
                self.send_error(sender_id = sender_id, x = x)
                pass

    def tweet_attachment(self, media_url = None, sender_id = None):
        img = requests.get(media_url, auth = OAuth1(client_key = config.consumer_key, client_secret = config.consumer_secret, resource_owner_key = config.access_token, resource_owner_secret = config.access_token_secret))
        filename = 'temp.jpg'
        if img.status_code == 200:
            with open(filename, 'wb') as image:
                for chunk in img:
                    image.write(chunk)
                media_ids = self.api.media_upload(filename).media_id
                return media_ids
        else:
            self.send_error(sender_id = sender_id, x = 'ERROR: Image not uploaded')
            pass

    def post_tweet_with_media(self, text = None, sender_id = None, type = None, media_url = None, link = None):
        if type == 'photo':
            media_ids = list()
            media_id = self.tweet_attachment(media_url = media_url, sender_id = sender_id)
            media_ids.append(media_id)
            text = ' '.join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)", " ",text).split())
            if len(text) > 280:
                tweet1 = 0
                while len(text) >280:
                    first = 0
                    last = 272
                    very_last = len(text)
                    split = text[260:last].split(' ')
                    tweet = text[first:last-len(split[-1])] + '(cont..)'
                    if tweet1 == 0:
                        try:
                            first_tweet = self.api.update_status(tweet, media_ids = media_ids)
                            tweet1 = first_tweet.id
                            try:
                                self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet1))
                            except Exception as x:
                                print(x)
                                pass
                        except Exception as x:
                            self.send_error(sender_id = sender_id, x = x)
                            pass
                    else:
                        try:
                            reply_tweet = self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
                            tweet1 = reply_tweet.id
                            time.sleep(2)
                        except Exception as x:
                            self.send_error(sender_id = sender_id, x = x)
                            pass
                    text = text[last-len(split[-1]):very_last]
                    tweet = text[first:last-len(split[-1])]
                    time.sleep(2)
                self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
            else:
                try:
                    tweet = self.api.update_status(status = text, media_ids = media_ids)
                    try:
                        self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet.id))
                    except Exception as x:
                        print(x)
                        pass
                except Exception as x:
                    print(x)
                    pass
        elif link != None:
            if 'photo' not in link:
                text = ' '.join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)", " ",text).split())
                if len(text) > 280:
                    tweet1 = 0
                    while len(text) >280:
                        first = 0
                        last = 272
                        very_last = len(text)
                        split = text[260:last].split(' ')
                        tweet = text[first:last-len(split[-1])] + '(cont..)'
                        if tweet1 == 0:
                            try:
                                first_tweet = self.api.update_status(tweet, attachment_url = link)
                                tweet1 = first_tweet.id
                                try:
                                    self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet1))
                                except Exception as x:
                                    print(x)
                                    pass
                            except Exception as x:
                                self.send_error(sender_id = sender_id, x = x)
                                pass
                        else:
                            try:
                                reply_tweet = self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
                                tweet1 = reply_tweet.id
                                time.sleep(2)
                            except Exception as x:
                                self.send_error(sender_id = sender_id, x = x)
                                pass
                        text = text[last-len(split[-1]):very_last]
                        tweet = text[first:last-len(split[-1])]
                        time.sleep(2)
                    self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
                else:
                    try:
                        tweet = self.api.update_status(status = text, attachment_url = link)
                        try:
                            self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet.id))
                        except Exception as x:
                            print(x)
                            pass
                    except Exception as x:
                        print(x)
                        pass
        else:
            self.send_error(sender_id = sender_id, x = 'ERROR: Wrong Attachment')

    def fit_text(self, text = None, max_width = 0, font = None):
        lines = list()
        if font.getsize(text)[0]  <= max_width:
            lines.append(text)
        else:
            words = text.split(' ')
            i = 0
            while i < len(words):
                line = ''
                while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                    line = line + words[i]+ " "
                    i += 1
                if not line:
                    line = words[i]
                    i += 1
                lines.append(line)
        return lines
    
    def upload_font_pic(self, text = None):
        y = 0
        filename = "temp.jpg"
        img = Image.new('RGB',(900,900),'white')
        font = ImageFont.truetype('Heebo-ExtraBold.ttf',round(75/(1+len(text)**(1/2))))
        print(round(75/(1+len(text)**(1/2))))
        w,h = font.getsize(text)
        draw = ImageDraw.Draw(img)
        lines = self.fit_text(text = text, max_width=900, font = font)
        for line in lines:
            draw.text((0,y), line, fill="black", font=font)
            y = y + h
        img = img.save(filename)
        media_ids = self.api.media_upload(filename).media_id
        return media_ids

    def post_font_pic(self, text = None, sender_id = None):
        media_ids = list()
        media_id = self.upload_font_pic(text=text)
        media_ids.append(media_id)
        try:
            tweet = self.api.update_status(status= config.trigger , media_ids = media_ids)
            tweet1 = tweet.id
            try:
                self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet1))
            except Exception as x:
                print(x)
                pass
        except Exception as x:
            self.send_error(sender_id = sender_id, x = x)
            pass

    def delete_DM(self,id):
        try:
            self.api.delete_direct_message(id)
        except Exception as x:
            print(x)
            pass