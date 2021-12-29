from twitivity import Activity
import config

def test_remove_subscription():
    activity = Activity()
    subscription_remove = activity.delete(webhook_id=config.webhook_id)
    print(subscription_remove)
    if subscription_remove.status_code != 204:
        print("NOT DELETED")
        pass

def test_list_subscription():
    activity = Activity()
    print(activity.webhooks())

def subscribe():
    activity = Activity()
    print(
        activity.register_webhook(
            callback_url=config.callback+"/webhook/twitter"
        )
    )
    print(activity.subscribe())

if __name__ == "__main__":
    test_remove_subscription()
    test_list_subscription()