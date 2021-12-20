from time import time
from bot import bot
import time
import config

def run():
    dmslist= list()
    while True:
        dmslist = bot.read_dm()
        if (len(dmslist) != 0):
            for x in range(len(dmslist)):
                if dmslist[x]['type'] == None and config.trigger in dmslist[x]['message']:
                    bot.post_tweet(text = dmslist[x]['message'], sender_id=dmslist[x]['sender_id'])
                elif dmslist[x]['type'] != None:
                    bot.post_tweet_with_media(text = dmslist[x]['message'], sender_id=dmslist[x]['sender_id'], link = dmslist[x]['link'], media_url=dmslist[x]['media_url'], type = dmslist[x]['type'])
                else:
                    dmslist[x]['message'] = dmslist[x]['message'].replace(config.trigger_text_to_pic, "")
                    bot.post_font_pic(text = dmslist[x]['message'], sender_id=dmslist[x]['sender_id'])
                time.sleep(1)
            time.sleep(29)
            for x in range(len(dmslist)):
                bot.delete_DM(dmslist[x]['id'])
            time.sleep(30)
        else:
            time.sleep(60)
            
if __name__ == "__main__":
    bot = bot()
    run()


                    