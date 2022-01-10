from time import time
from bot import bot
from twitivity import Event
from tinydb import TinyDB, Query
import time, config, json, flask, json, hmac, hashlib, base64, logging,config, os

logging.basicConfig(
    filename="app.log",
    filemode="w",
    level=logging.INFO,
)

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
        logging.info(data)
        if "direct_message_events" in data.keys():
            to_post = TinyDB('to_post.json')
            message = data['direct_message_events'][0]['message_create']['message_data']['text']
            sender_id = data['direct_message_events'][0]['message_create']['sender_id']
            link = None
            media_url = None
            _type = None
            if config.trigger in message.lower():
                if len(message) >= 16:
                    if 'attachment' in data['direct_message_events'][0]['message_create']['message_data']:
                        if data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['type'] == 'photo':
                            _type="photo"
                            media_url = data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['media_url']
                        elif data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['type'] == 'animated_gif':
                            #need fix
                            _type="photo"
                            media_url = data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['media_url']
                        elif data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['type'] == 'video':
                            #need fix
                            _type="photo"
                            media_url = data['direct_message_events'][0]['message_create']['message_data']['attachment']['media']['media_url']
                    elif len(data['direct_message_events'][0]['message_create']['message_data']['entities']['urls'])>0:
                        #this is hare other tweets
                        if data['direct_message_events'][0]['message_create']['message_data']['entities']['urls'][0]['expanded_url'][8] == 't' and data['direct_message_events'][0]['message_create']['message_data']['entities']['urls'][0]['expanded_url'][8] == 'w':
                            _type="link"
                            link = data['direct_message_events'][0]['message_create']['message_data']['entities']['urls'][0]['expanded_url']
                        else:
                            #link other than to twitter
                            _type="linkout"
                    else:
                        _type = "text"
                    to_post.insert({"index":(to_post.__len__()),"user_id":sender_id,"message" : message, "link":link, "media_url":media_url, "type": _type})
                    process(sender_id)
                else:
                    bot.send_error(sender_id = sender_id, x = "menfess yang Anda ingin kirimkan perlu mengandung minimal 16 huruf agar dapat dikirimkan")
            elif config.trigger_text_to_pic in message.lower():
                if len(message) >= 16:
                    if len(message) < 1230:
                        to_post.insert({"index":(to_post.__len__()),"user_id":sender_id,"message" : message, "link":link, "media_url":media_url, "type": "tweet2pic"})
                        process(sender_id)
                    else:
                        bot.send_error(sender_id = sender_id, x = "menfess yang Anda ingin dikirimkan mengandung terlalu banyak huruf")
                else:
                    bot.send_error(sender_id = sender_id, x = "menfess yang Anda ingin dikirimkan perlu mengandung minimal 16 huruf agar dapat dikirimkan")
            elif config.trigger_delete in message.lower() and len(message) <=16:
                delete_tweet(sender_id=sender_id,timestamp=data['direct_message_events'][0]['created_timestamp'])
            to_post.close()
        elif "tweet_create_events" in data.keys():
            if config.trigger_report in data['tweet_create_events'][0]['text']:
                bot.send_report(tweet_id=data['tweet_create_events'][0]['in_reply_to_status_id_str'], recipient_id=config.report_recipient)
        return {"code": 200}

def process(sender_id: int):
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
    if round_old.get(User.index==0).get('min')< round_num['min'] or round_old.get(User.index==0).get('hour') < round_num['hour']:
        round_old.update({"min":min}, User.index == 0)
        round_old.update({"hour":hour}, User.index == 0)
        with open("count.txt","w") as x:
            x.truncate()
    if sum(1 for line in open('count.txt')) <8:
        post = True
    else:
        post = False
    if post == False:
        to_post = TinyDB('to_post.json')
        to_post.truncate()
        bot.send_error(sender_id = sender_id, x = ("batas tweet kami telah tercapai. Mohon coba lagi pada jam "+ str(round_up["hour"])+":"+str(round_up["min"])))
        to_post.close()
    else:
        run()
    round_old.close()
    
def run():
    to_post = TinyDB('to_post.json')
    tweet_sender_id = list()
    tweet_ids= list()
    message_list = list()
    to_post_len = to_post.__len__()
    if to_post_len>0:
        for x in range(to_post.__len__()):
            message_list.append(to_post.get(User.index == 0).get('message'))
            if to_post.get(User.index == 0).get('type') == "tweet2pic":
                to_post.update({'message': to_post.get(User.index == 0).get('message').replace(config.trigger_text_to_pic, "")}, User.index==0)
                tweet = bot.post_font_pic(text = to_post.get(User.index == 0).get('message'), sender_id=to_post.get(User.index == 0).get('user_id'))
                tweet_sender_id.append(to_post.get(User.index == 0).get('user_id'))
                tweet_ids.append(tweet['id'])
            else:
                tweet = bot.post_tweet(text = to_post.get(User.index == 0).get('message'), sender_id=to_post.get(User.index == 0).get('user_id'), link = to_post.get(User.index == 0).get('link'), media_url=to_post.get(User.index == 0).get('media_url'), type = to_post.get(User.index == 0).get('type'))
                tweet_sender_id.append(to_post.get(User.index == 0).get('user_id'))
                tweet_ids.append(tweet['id'])
            to_post.remove(User.index==0)
            for y in range(to_post.__len__()):
                to_post.update({'index': y}, User.index == y+1)
        print('DONE')
    to_post.close()
    if len(tweet_sender_id)>0:
        db = TinyDB('database.json')
        for x in range(to_post_len):
            try:
                db.insert({"user_id":tweet_sender_id[x], "message" : message_list[x], "timestamp":round(time.time()*1000), "tweet_id":tweet_ids[x]})
            except Exception as x:
                print(x)
        db.close()

def delete_tweet(sender_id:int, timestamp:int):
    User = Query()
    db = TinyDB('database.json')
    if (db.search(User.user_id==sender_id)[-1].get('timestamp')+900000 > int(timestamp)):
        try:
            bot.delete_tweet(db.search(User.user_id==sender_id)[-1].get('tweet_id'), sender_id = sender_id)
            db.remove(User.tweet_id==db.search(User.user_id==sender_id)[-1].get('tweet_id'))
        except Exception as x:
            bot.send_error(sender_id=sender_id,x=x)
            pass
    else:
        bot.send_DM(message="[BOT] Maaf, Anda tidak dapat menghapus menfess Anda saat ini.", user_id = sender_id)
    db.close()

def init():
    round_old = TinyDB('round_old.json')
    round_old.truncate()
    round_old.insert({"index":0, "min":0, "hour" : 0})
    round_old.close()
    to_post = TinyDB('to_post.json')
    to_post.truncate()
    to_post.close()

if __name__ == "__main__":
    bot = bot()
    User = Query()
    init()
    port = int(os.environ.get('PORT', 51155))
    app.run(host="0.0.0.0", port=port)