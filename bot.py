import tweepy, config, time, requests, re
from requests_oauthlib import OAuth1
from PIL import Image, ImageDraw, ImageFont


class bot:
    def __init__(self):
        self.auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
        self.auth.set_access_token(config.access_token, config.access_token_secret)
        self.api = tweepy.API(self.auth, parser=tweepy.parsers.JSONParser())
        self.trigger = config.trigger
        self.trigger2 = config.trigger_text_to_pic

    def get_dms(self):
        print("im here")
        dms = self.api.get_direct_messages()
        return dms

    def send_error(self, sender_id = None, x = None):
        try:
            self.api.send_direct_message(recipient_id = sender_id, text=('[BOT] ERROR karena '+x))
            print(x)
        except Exception as x:
            self.api.send_direct_message(recipient_id = sender_id, text=('[BOT] ERROR'))
            print(x)

    def send_DM(self, message, user_id):
        try:
            self.api.send_direct_message(recipient_id=user_id, text=message)
        except Exception as X:
            self.send_error(sender_id=user_id, x=X)
            pass

    def post_tweet(self, text = None, sender_id = None, type = None, media_url = None, link = None):
        media_ids = list()
        if type == 'photo':
            media_id = self.tweet_attachment(media_url = media_url, sender_id = sender_id)
            media_ids.append(media_id)
            text = ' '.join(re.sub("(@[A-Za-z0-9]+)|(\w+:\/\/\S+)", " ",text).split())
        elif type == 'link':
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
                        tweet = self.api.update_status(tweet, media_ids = media_ids, attachment_url = link)
                        tweet1 = tweet['id']
                        with open("count.txt","a") as x:
                            x.write("a\n")
                        try:
                            self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet1))
                            pass
                        except Exception as x:
                            print(x)
                            pass
                    except Exception as x:
                        self.send_error(sender_id = sender_id, x = x)
                        pass
                    time.sleep(2)
                else:
                    try:
                        reply_tweet = self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
                        tweet1 = reply_tweet['id']
                        with open("count.txt","a") as x:
                            x.write("a\n")
                        pass
                    except Exception as x:
                        self.send_error(sender_id = sender_id, x = x)
                        pass
                    time.sleep(4)
                time.sleep(2)
                text = text[last-len(split[-1]):very_last]
                tweet = text[first:last-len(split[-1])]
            self.api.update_status(tweet, in_reply_to_status_id = tweet1, auto_populate_reply_metadata = True)
            return tweet
        else:
            try:
                tweet = self.api.update_status(status=text, media_ids = media_ids, attachment_url = link)
                with open("count.txt","a") as x:
                    x.write("a\n")
                try:
                    self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet['id']))
                    pass
                except Exception as x:
                    print(x)
                    pass
                return tweet
            except Exception as x:
                self.send_error(sender_id = sender_id, x = x)
                pass

    def tweet_attachment(self, media_url = None, sender_id = None):
        img = requests.get(media_url, auth = OAuth1(client_key = config.consumer_key, client_secret = config.consumer_secret, resource_owner_key = config.access_token, resource_owner_secret = config.access_token_secret))
        filename = 'temp.png'
        if img.status_code == 200:
            with open(filename, 'wb') as image:
                for chunk in img:
                    image.write(chunk)
                media_ids = self.api.media_upload(filename)['media_id']
                return media_ids
        else:
            self.send_error(sender_id = sender_id, x = 'gambar gagal ter-upload')
            pass

    def fit_text(self, text = None, max_width = 0, font = None):
        lines = list()
        product = list()
        if font.getsize(text)[0]  <= max_width:
            product.append(text)
        else:
            paragraph = list()
            paragraph = text.splitlines()
            if '' in paragraph:
                paragraph.remove('')
            for x in range(len(paragraph)):
                lines.append(paragraph[x].split(' '))
            i = 0
            e = 0
            while i < len(paragraph):
                line = ''
                while e < len(lines[i]) and font.getsize(line + lines[i][e])[0] <= max_width:
                    line = line + lines[i][e]+ " "
                    e += 1
                if not line:
                    line = lines[i][e]
                    e += 1
                if e == len(lines[i]):
                    e = 0
                    i +=1
                product.append(line)
        return product
    
    def upload_font_pic(self, text = None):
        x_offset = 40
        filename = 'temp.png'
        ptnmenfess = Image.open('ptnmenfess.png').convert('RGBA')
        img = Image.new('RGB',(900,900),'white')
        font_size = round(150/(1+(len(text)*0.01)**(1/2)))
        font = ImageFont.truetype('arial.ttf',font_size)
        w, h = font.getsize(text)
        draw = ImageDraw.Draw(img)
        lines = self.fit_text(text = text, max_width=900 - x_offset, font = font)
        ptnmenfess.thumbnail((w,h))
        ptn_w, ptn_h = ptnmenfess.size
        img.paste(ptnmenfess, (875-round(ptn_w), 875-round(ptn_h)), ptnmenfess)
        y = 900/2 - len(lines)*h/2
        for line in lines:
            draw.text((x_offset,y), line, fill="black", font=font)
            y = y + h
        img = img.save(filename)
        media_ids = self.api.media_upload(filename)['media_id']
        return media_ids

    def post_font_pic(self, text = None, sender_id = None):
        media_ids = list()
        media_id = self.upload_font_pic(text=text)
        media_ids.append(media_id)
        try:
            tweet = self.api.update_status(status= config.trigger , media_ids = media_ids)
            with open("count.txt","a") as x:
                x.write("a\n")
            tweet1 = tweet['id']
            try:
                self.api.send_direct_message(recipient_id=sender_id, text='[BOT] Tweet berhasil dipublikasikan ' + 'https://twitter.com/'+ config.username +'/status/' + str(tweet1))
            except Exception as x:
                print(x)
                pass
            return tweet
        except Exception as x:
            self.send_error(sender_id = sender_id, x = x)
            pass

    def delete_DM(self,id):
        try:
            self.api.delete_direct_message(id)
        except Exception as x:
            print(x)
            pass
        
    def delete_tweet(self, tweet_id:int = None, sender_id:int=None):
        try:
            self.api.destroy_status(tweet_id)
            self.send_DM(user_id=sender_id, message="Tweet anda berhasil dihapus!")
        except Exception as x:
            self.send_error(user_id=sender_id, message="ada sebuah kesalahan. Coba tunggu lagi beberapa menit")

    def send_report(self, tweet_id:str, recipient_id:int):
        try:
            self.api.send_direct_message(recipient_id=recipient_id, text='[BOT] Tweet ini dilaporkan ' + 'https://twitter.com/'+ config.username +'/status/' + tweet_id)
        except Exception as x:
            print(x)