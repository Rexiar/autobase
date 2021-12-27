from twitivity import Activity
import config
if __name__ == "__main__":
    activity = Activity()
    print(
        activity.register_webhook(
            callback_url=config.callback+"/twitter/callback"
        )
    )
    print(activity.subscribe())