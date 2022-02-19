from twitivity import Activity
import config

def remove_subscription():
    activity = Activity()
    env = activity.webhooks()
    print(env)
    activity = Activity()
    subscription_remove = activity.delete(webhook_id=env['environments'][0]['webhooks'][0]['id'])
    print(subscription_remove)
    if subscription_remove.status_code != 204:
        print("NOT DELETED")
        pass
    else:
        print("DELETED")

if __name__ == "__main__":
    remove_subscription()