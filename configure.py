from twitivity import Activity
import json

if __name__ == "__main__":
    activity = Activity()
    print(
        activity.register_webhook(
            callback_url="https://02cd-36-72-218-251.ngrok.io/twitter/callback"
        )
    )
    print(activity.subscribe())