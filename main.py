import tweepy, config, json, requests, re, time
from tinydb import TinyDB, Query
from requests_oauthlib import OAuth1
from PIL import ImageDraw, Image, ImageFont
import flask, hmac, hashlib, base64, os


app = flask.Flask(__name__)

consumer_secret = config.consumer_secret

@app.route('/')
def default_route():
    return flask.send_from_directory('www', 'index.html')  

@app.route("/webhook/twitter", methods=["GET", "POST"])
def callback() -> json:
    if flask.request.method == "GET" or flask.request.method == "PUT":
        hash_digest = hmac.digest(
            key=config.consumer_secret.encode("utf-8"),
            msg=flask.request.args.get("crc_token").encode("utf-8"),
            digest=hashlib.sha256,
        )
        return {
            "response_token": "sha256="
            + base64.b64encode(hash_digest).decode("ascii")
        }
    elif flask.request.method == "POST":
        data = flask.request.get_json()
        if "direct_message_events" in data.keys():
            if data['direct_message_events'][0]['message_create']['target']['recipient_id'] == str(config.base_id):
                message = data['direct_message_events'][0]['message_create']['message_data']['text']
                sender_id = data['direct_message_events'][0]['message_create']['sender_id']
                state = test_state(sender_id=sender_id)
                if config.trigger_start not in message.lower() and config.trigger_delete not in message.lower() and config.trigger_start not in message.lower():
                    message = message.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&")
                    if state == "new" and (config.trigger_message in message.lower() or config.trigger_poll in message.lower() or config.trigger_picture in message.lower()):
                        try:
                            following = api.get_friendship(source_id=config.base_id, target_id= sender_id)[0].followed_by
                        except Exception as x:
                            print(x)
                            following = True
                        
                        if following:
                            if message == config.trigger_message:
                                db = TinyDB("database.json")
                                db.update({"state": "message"}, user.sender_id == sender_id)
                                db.close()
                                get_message(sender_id)
                            elif message == config.trigger_poll:
                                db = TinyDB("database.json")
                                db.update({"state": "poll"}, user.sender_id == sender_id)
                                db.close()
                                get_poll(sender_id)
                            elif message == config.trigger_picture:
                                db = TinyDB("database.json")
                                db.update({"state": "picture"}, user.sender_id == sender_id)
                                db.close()
                                get_picture(sender_id)
                            else:
                                menu(sender_id, data['users'][str(sender_id)]['name'])
                        else:
                            api.send_direct_message(recipient_id=sender_id, text="Maaf, kamu perlu follow bot ini untuk mengirim menfess.")
                            menu(sender_id, data['users'][str(sender_id)]['name'])
                
                    elif state == "message":
                        if len(message) >= 16:
                            safe = banned_words(message)
                            attachment(data)
                            is_time, time_round = process()
                            to_post(message, safe, is_time, sender_id, state, data['direct_message_events'][0]['created_timestamp'], time_round, data['users'][str(sender_id)]['name'])
                        else:
                            api.send_direct_message(recipient_id=sender_id, text="Maaf, menfess yang Anda ingin kirimkan perlu mengandung minimal 16 huruf agar dapat dikirimkan")
                            menu(sender_id, data['users'][str(sender_id)]['name'])

                    elif state == "poll":
                        if len(message) >= 16:
                            safe = banned_words(message)
                            attachment(data)
                            is_time, time_round = process()
                            post, message, options = polls(message=message, sender_id=sender_id, username=data['users'][str(sender_id)]['name'])
                            if post:
                                to_post(message=message, safe=safe, is_time=is_time, sender_id=sender_id, state=state, now=data['direct_message_events'][0]['created_timestamp'], time_round=time_round, username=data['users'][str(sender_id)]['name'], poll_options=options)
                            else:
                                menu(sender_id, data['users'][str(sender_id)]['name'])
                        else:
                            api.send_direct_message(recipient_id=sender_id, text="Maaf, menfess yang Anda ingin kirimkan perlu mengandung minimal 16 huruf agar dapat dikirimkan")
                            menu(sender_id, data['users'][str(sender_id)]['name'])

                    elif state == "picture":
                        if len(message)>=16:
                            safe = banned_words(message)
                            picture_text(text=message,sender_id=sender_id)
                            is_time, time_round = process()
                            to_post("", safe, is_time, sender_id, state, data['direct_message_events'][0]['created_timestamp'], time_round, data['users'][str(sender_id)]['name'])
                        else:
                            api.send_direct_message(recipient_id=sender_id, text="Maaf, menfess yang Anda ingin kirimkan perlu mengandung minimal 16 huruf agar dapat dikirimkan")
                            menu(sender_id, data['users'][str(sender_id)]['name'])

                    else:
                        menu(sender_id, data['users'][str(sender_id)]['name'])
                
                elif config.trigger_delete in message.lower():
                    delete(sender_id, data['direct_message_events'][0]['created_timestamp'])
                    menu(sender_id, data['users'][str(sender_id)]['name'])

                else:
                    menu(sender_id, data['users'][str(sender_id)]['name'])
        return {"code": 200}

def menu(sender_id:str = None, name:str = None, tweet_id:str = None):
    db = TinyDB("database.json")
    db.update({"state" : "new", "message" : "", "type" : "", "url" : ""}, user.sender_id == sender_id)
    db.close()
    quick_reply = [
                {
                        "label": config.trigger_message,
                        "description": "Aku mau mengirim menfess tulisan biasa.",
                        "metadata": "external_id_1"
                },
                {
                        "label": config.trigger_poll,
                        "description": "Aku mau mengirim menfess polls.",
                        "metadata": "external_id_2"
                },
                {
                        "label": config.trigger_picture,
                        "description": "Aku mau mengirim menfess tulisanku di gambar.",
                        "metadata": "external_id_2"
                },
                {
                        "label": config.trigger_delete,
                        "description": "Tolong hapus menfessku yang barusan aku kirim",
                        "metadata": "external_id_4"
                }
    ]
    if tweet_id != None:
        message = "Menfessmu berhasil di-post! Anda dapat menghapusnya dalam 15 menit ke depan dengan mengetik " +config.trigger_delete +"\n- - - - -\nHalo, "+ name + "✨, Anda dapat mengirimkan tiga jenis menfess, yaitu menfess biasa, menfess polls, dan menfess gambar (tulisanmu dituliskan di gambar) ✍️"+' https://twitter.com/'+ config.username +'/status/' + str(tweet_id)
        api.send_direct_message(recipient_id=sender_id, text=message, quick_reply_options=quick_reply)
    else:
        message = "Halo, "+ name + "✨, Anda dapat mengirimkan tiga jenis menfess, yaitu menfess biasa, menfess polls, dan menfess gambar (tulisanmu dituliskan di gambar) ✍️"
        api.send_direct_message(recipient_id=sender_id, text=message, quick_reply_options=quick_reply)

def test_state(sender_id:int)->str:
    db = TinyDB("database.json")
    try:
        state = db.get(user.sender_id == sender_id).get('state')
        db.close()
        return state
    except:
        db.insert({"sender_id" : sender_id, "state" : "new", "message" : "", "type" : "", "url" : "" , "tweet_id" : 0, "tweet_time" : 0})
        db.close()
        return "new"

def get_message(sender_id:int):
    try:
        api.send_direct_message(recipient_id=sender_id, text="Apa pesan menfess yang Anda ingin kirimkan?\n- - - - -\nKetik '/menu' untuk kembali ke menu.")
    except Exception as x:
        print(x)

def get_poll(sender_id:int):
    try:
        api.send_direct_message(recipient_id=sender_id, text="Apa pertanyaan yang Anda ingin untuk di-polling-kan beserta pilihan-pilihannya?\n- - - - -\nIni tweet petunjuk pengiriman menfess polls. (Anda tidak perlu memberikan triggernya sekarang).\n- - - - -\nKetik '/menu' untuk kembali ke menu. https://twitter.com/ptnmenfess/status/1484366264311365633")
    except Exception as x:
        print(x)
    #get poll options

def get_picture(sender_id:int):
    try:
        api.send_direct_message(recipient_id=sender_id, text="Apa pesan yang Anda ingin untuk dituliskan di gambar?\n- - - - -\nKetik '/menu' untuk kembali ke menu.")
    except Exception as x:
        print(x)

def delete(sender_id:int = None, now:int = None):
    db = TinyDB('database.json')
    tweet_id = db.get(user.sender_id==sender_id).get("tweet_id")
    tweet_time = db.get(user.sender_id==sender_id).get("tweet_time")
    db.update({"state" : "new", "message" : "", "type" : "", "url" : "" , "tweet_id" : 0, "tweet_time" : 0}, user.sender_id == sender_id)
    db.close()
    if int(tweet_time) + 900000 > int(now):
        try:
            client.delete_tweet(tweet_id)
            try:
                api.send_direct_message(recipient_id = sender_id, text = "Menfessmu berhasil dihapus.")
            except Exception as x:
                print(x)
        except Exception as x:
            print(x)
    else:
        try:
            api.send_direct_message(recipient_id=sender_id, text="Maaf, kamu sudah tidak bisa menghapus menfess kamu sekarang.")
        except Exception as x:
            print(x)

def banned_words(message:str)->bool:
    safe = True
    for x in range(len(config.banned_words)):
        if config.banned_words[x] in message.lower():
            safe = False
    return safe

def attachment(data):
    type = ""
    url = ""
    if "attachment" in data['direct_message_events'][0]['message_create']['message_data']:
        type = data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['type']
        if type == "animated_gif":
            url = data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['video_info']['variants'][0]['url']
        else:
            url = data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['media_url']
        db = TinyDB('database.json')
        db.update({"type" : type , "url" : url}, user.sender_id == data['direct_message_events'][0]['message_create']['sender_id'])
        db.close()

def process():
    round_old = TinyDB('round_old.json')
    hour, min = map(int, time.strftime("%H %M").split())
    round_num = {"hour" : hour, "min" : min-(min%5)}
    round_up = []
    if hour==23 and min>=55:
        round_up = {"hour":00,"min":00}
    elif min>=55:
        round_up = {"hour":hour+1,"min":00}
    else:
        round_up = {"hour" : hour, "min" : min-(min%5)+5}
    if round_old.get(doc_id=1).get('min')< round_num['min'] or round_old.get(doc_id=1).get('hour') < round_num['hour']:
        round_old.update({"min":min, "hour":hour}, doc_ids = [1])
        with open("count.txt","w") as x:
            x.truncate()
    round_old.close()
    if sum(1 for line in open('count.txt')) <8:
        post = True
    else:
        post = False
    return post, round_up

def to_post(message:str, safe:bool, is_time:bool, sender_id:int, state:str, now, time_round, username, poll_options = None):
    #username = data['users'][str(sender_id)]['name']
    message = re.sub("#[A-Za-z0-9_]+","", message).replace("@","@.")
    if safe and is_time:
        db = TinyDB("database.json")
        db.update({"message": message}, user.sender_id == sender_id)
        db.close()
        post(sender_id, now, username, poll_options)
    elif not safe:
        api.send_direct_message(recipient_id=sender_id, text="Menfess kamu mengandung kata yang terlarang. Coba tulis menfess baru.")
        menu(sender_id, username)
    else:
        api.send_direct_message(recipient_id=sender_id, text="Maaf, batas kirim menfess kami telah tercapai. Mohon coba lagi pada jam "+ str(time_round["hour"])+":"+str(time_round["min"]))
        menu(sender_id, username)

def post(sender_id:int, now:int, username:str, poll_options = None):

    if poll_options != None:
        poll_time = 60
    else:
        poll_time = None

    db = TinyDB('database.json')
    type = db.get(user.sender_id==sender_id).get("type")
    url = db.get(user.sender_id==sender_id).get("url")
    media_ids = None

    #uploads media if there is
    if type == "animated_gif":
        try:
            media_ids = [upload_media(type, url)]
            message = ' '.join(re.sub(r'http\S+', '', db.get(user.sender_id==sender_id).get("message")).split())
            db.update({"message" : message, "url" : "" }, user.sender_id == sender_id)
        except:
            pass
    elif type == "photo":
        try:
            media_ids = [upload_media(type, url)]
            message = ' '.join(re.sub(r'http\S+', '', db.get(user.sender_id==sender_id).get("message")).split())
            db.update({"message" : message, "url" : "" }, user.sender_id == sender_id)
        except:
            pass
    elif type == "video":
        try:
            media_ids = [upload_media(type, url)]
            message = ' '.join(re.sub(r'http\S+', '', db.get(user.sender_id==sender_id).get("message")).split())
            db.update({"message" : message, "url" : "" }, user.sender_id == sender_id)
        except:
            pass
    elif type == "picture_text":
        try:
            media_ids = [upload_media(type)]
        except:
            pass
    
    url = db.get(user.sender_id==sender_id).get("url")
    if url == "":
        url = None

    #actually sending the message
    text = db.get(user.sender_id==sender_id).get("message")
    db.close()
    if len(text) > 280:
        reply_to = 0
        while len(text) >275:
            split = text[255:267].split(' ')
            tweet = text[0:267-len(split[-1])] + '(cont..)'
            if reply_to == 0:
                try:
                    #first tweet
                    #first_tweet = api.update_status(tweet, media_ids = media_ids, attachment_url = url)
                    first_tweet = client.create_tweet(text=tweet, media_ids=media_ids, poll_options=poll_options, poll_duration_minutes=poll_time)
                    reply_to = first_tweet.data["id"]
                    with open("count.txt","a") as x:
                        x.write("a\n")
                    try:
                        menu(sender_id=sender_id, name= username, tweet_id=reply_to)
                    except Exception as x:
                        print(x)
                except Exception as x:
                    api.send_direct_message(recipient_id=sender_id, text="Gagal mengirimkan menfessmu. Coba lagi sebentar lagi.")
                    print(x)
                time.sleep(1)
            else:
            #tweets between first and last
                try:
                    #reply_tweet = api.update_status(tweet, in_reply_to_status_id = reply_to, auto_populate_reply_metadata = True)
                    reply_tweet = client.create_tweet(text=tweet, in_reply_to_tweet_id=reply_to)
                    reply_to = reply_tweet.data["id"]
                    with open("count.txt","a") as x:
                        x.write("a\n")
                except Exception as x:
                    print(x)
                time.sleep(1)
            text = text[267-len(split[-1]):len(text)]
            tweet = text[0:267-len(split[-1])]
        #last tweet
        try:
            reply_tweet = client.create_tweet(text=tweet, in_reply_to_tweet_id=reply_to)
            reply_to = reply_tweet.data["id"]
            with open("count.txt","a") as x:
                x.write("a\n")
            db = TinyDB('database.json')
            db.update({"tweet_id":first_tweet.data["id"], "tweet_time":now}, user.sender_id == sender_id)
            db.close()
        except Exception as x:
                print(x)

    else:
        try:
            tweet_id = client.create_tweet(text=text, media_ids=media_ids, poll_options=poll_options, poll_duration_minutes=poll_time).data["id"]
            try:
                menu(sender_id=sender_id, name=username , tweet_id=tweet_id)
            except Exception as x:
                print(x)
            db = TinyDB('database.json')
            db.update({"tweet_id":tweet_id, "tweet_time":now}, user.sender_id == sender_id)
            db.close()
            with open("count.txt","a") as x:
                x.write("a\n")
        except Exception as x:
            print(x)
            try:
                api.send_direct_message(recipient_id = sender_id, text = "Gagal mengirimkan menfessmu. Coba lagi sebentar lagi.")
            except Exception as x:
                print(x)

def upload_media(type:str = None, url:str = None):
    if type == "animated_gif":
        filename = 'gif.mp4'
        with open(filename,'wb') as f:
            f.write(requests.get(url,auth = OAuth1(client_key = config.consumer_key, client_secret = config.consumer_secret, resource_owner_key = config.access_token, resource_owner_secret = config.access_token_secret)).content)
        media_id = api.media_upload(filename).media_id
        return media_id
    elif type == "picture_text":
        filename = 'media.png'
        media_id = api.media_upload(filename).media_id
        return media_id
    else:
        filename = 'media.png'
        with open(filename,'wb') as f:
            f.write(requests.get(url,auth = OAuth1(client_key = config.consumer_key, client_secret = config.consumer_secret, resource_owner_key = config.access_token, resource_owner_secret = config.access_token_secret)).content)
        media_id = api.media_upload(filename).media_id
        return media_id

def polls(message:str, sender_id:int, username:str):
    good = True
    product = message.split('/')
    for x in product:
        if '/' in product:
            product[x].replace('/','')
    message = product[0]
    product.pop(0)
    choice = product

    if len(message) <280:
        if len(choice) <=4 and len(choice) > 0:
            
            for x in range(len(choice)):
                if len(choice[x])>=25:
                    good = False
            
            if good:
                poll_fail = False
            else:
                poll_fail=True
                try:
                    api.send_direct_message(recipient_id = sender_id, text = "Maaf, poll yang Anda coba kirimkan mengandung pilihan yang memiliki lebih dari 25 huruf. Coba hapus beberapa huruf untuk salah satu pilihan.")
                except Exception as x:
                    print(x)
        
        else:
            poll_fail = True
            try:
                api.send_direct_message(recipient_id = sender_id, text = "Maaf, poll yang Anda coba kirimkan mengandung jumlah pilihan yang salah. Polls hanya dapat mengirimkan antara 1-4 pilihan.")
            except Exception as x:
                print(x)
    
    else:
        poll_fail = True
        try:
            api.send_direct_message(recipient_id = sender_id, text = "Maaf, poll yang Anda coba kirimkan mengandung pertanyaan yang mengandung terlalu banyak huruf. Coba hapus beberapa huruf untuk pertanyaannya.")
        except Exception as x:
            print(x)

    return not poll_fail, message, choice

def fit_text(text = None, max_width = 0, font = None):
    lines = list()
    product = list()
    if font.getsize(text)[0]  <= max_width:
        product.append(text)
    else:
        paragraph = list()
        paragraph = text.splitlines()
        if '' in paragraph:
            paragraph.remove('')
        clean_paragraph = 0
        for x in range(len(paragraph)):
            if (paragraph[x]!=""):
                lines.append(paragraph[x].split(' '))
                clean_paragraph+=1
        i = 0
        e = 0
        while i < clean_paragraph:
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
    
def picture_text(text:str, sender_id:int):
    x_offset = 40
    filename = 'media.png'
    ptnmenfess = Image.open('ptnmenfess.png').convert('RGBA')
    img = Image.new('RGB',(900,900),'white')
    font_size = round(150/(1+(len(text)*0.01)**(1/2)))
    font = ImageFont.truetype('Lato-Bold.ttf',font_size)
    w, h = font.getsize(text)
    draw = ImageDraw.Draw(img)
    lines = fit_text(text = text, max_width=900 - x_offset, font = font)
    ptnmenfess.thumbnail((round(w/2),round(h/2)))
    ptn_w, ptn_h = ptnmenfess.size
    img.paste(ptnmenfess, (875-round(ptn_w), 875-round(ptn_h)), ptnmenfess)
    y = 900/2 - len(lines)*h/2
    for line in lines:
        draw.text((x_offset,y), line, fill="black", font=font)
        y = y + h
    img = img.save(filename)
    db = TinyDB("database.json")
    db.update({"message": "","type": "picture_text"}, user.sender_id == sender_id)
    db.close()

if __name__ == "__main__":
    user = Query()
    api = tweepy.API(tweepy.OAuth1UserHandler(config.consumer_key, config.consumer_secret, config.access_token, config.access_token_secret))
    client = tweepy.Client(bearer_token=config.bearer_token, consumer_key= config.consumer_key, consumer_secret= config.consumer_secret, access_token= config.access_token, access_token_secret= config.access_token_secret)
    port = int(os.environ.get('PORT', 51155))
    app.run(host="0.0.0.0", port=port)