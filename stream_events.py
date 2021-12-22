import json

from twitivity import Event
from pprint import pprint


class StreamEvent(Event):
    CALLBACK_URL: str = "https://02cd-36-72-218-251.ngrok.io/twitter/callback"

    def on_data(self, data: json) -> None:
        pprint(data, indent=2)


if __name__ == "__main__":
    stream_event = StreamEvent()
    stream_event.listen()