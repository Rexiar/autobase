from time import time
from bot import bot
import time
import config

def run():
    dmslist= list()
    while True:
        dmslist = bot.read_dm()
        if (len(dmslist) != 0):
            print('*')
            for x in range(len(dmslist)):
                if dmslist[x]['type'] == "tweet2pic":
                    dmslist[x]['message'] = dmslist[x]['message'].replace(config.trigger_text_to_pic, "")
                    bot.post_font_pic(text = dmslist[x]['message'], sender_id=dmslist[x]['sender_id'])
                else:
                    bot.post_tweet(text = dmslist[x]['message'], sender_id=dmslist[x]['sender_id'], link = dmslist[x]['link'], media_url=dmslist[x]['media_url'], type = dmslist[x]['type'])
                time.sleep(5)
            for x in range(len(dmslist)):
                bot.delete_DM(dmslist[x]['id'])
        else:
            time.sleep(60)
            
if __name__ == "__main__":
    bot = bot()
    run()


                    