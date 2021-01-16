import datetime
import json
import os
import time

import durations
import pytz
import requests
from dateutil import parser
from dotenv import load_dotenv

load_dotenv()

# commets

class TimeManagement:

    def __init__(self):
        self.nightscout_json = requests.get("{}api/v1/entries.json?count=1".format(os.getenv("NIGHTSCOUT_URL"))).json()
        self.timezone = os.getenv("TIMEZONE_DIFFERENCE")
        self.nightscout_gmt = parser.parse(self.nightscout_json[0]["dateString"]).replace(tzinfo=None)
        self.now_gmt = parser.parse(datetime.datetime.strftime(datetime.datetime.now(pytz.timezone("GMT")), "%H:%M:%S"))

    def timezone_converter(self):
        if self.timezone == 0:
            return [self.now_gmt, self.nightscout_gmt]
        else:
            if self.timezone.startswith("+"):
                difference = int(self.timezone[1:])
                return [datetime.datetime.strftime((self.now_gmt + datetime.timedelta(hours=difference)),
                                                   "%H:%M:%S"),
                        datetime.datetime.strftime((self.nightscout_gmt + datetime.timedelta(hours=difference)),
                                                   "%H:%M:%S")]
            elif self.timezone.startswith("-"):
                difference = int(self.timezone[1:])
                return [datetime.datetime.strftime((self.now_gmt - datetime.timedelta(hours=difference)),
                                                   "%H:%M:%S"),
                        datetime.datetime.strftime((self.nightscout_gmt - datetime.timedelta(hours=difference)),
                                                   "%H:%M:%S")]
            else:
                raise ValueError


class HueOperations:

    def __init__(self):
        self.hue_api_link = "http://{0}/api/{1}/".format(os.getenv("PHILLIPS_IP"), os.getenv("PHILLIPS_USERNAME"))
        self.colors = {
            "RED": {
                "hue": 10,
                "sat": 240,
                "bri": int(os.getenv("BRIGHTNESS_LEVEL"))},
            "ORANGE": {
                "hue": 4500,
                "sat": 250,
                "bri": int(os.getenv("BRIGHTNESS_LEVEL"))},
            "GREEN": {
                "hue": 27000,
                "sat": 250,
                "bri": int(os.getenv("BRIGHTNESS_LEVEL"))},
            "BLUE": {
                "hue": 45000,
                "sat": 250,
                "bri": int(os.getenv("BRIGHTNESS_LEVEL"))},
            "PURPLE": {
                "hue": 50000,
                "sat": 250,
                "bri": int(os.getenv("BRIGHTNESS_LEVEL"))
            }

        }

    def get_color(self, glucose_level: str):
        if glucose_level.upper().strip() == "HIGH":
            color = self.colors[str(os.getenv("HIGH_COLOR")).upper()]
        elif glucose_level.upper().strip() == "RANGE":
            color = self.colors[str(os.getenv("RANGE_COLOR")).upper()]
        elif glucose_level.upper().strip() == "DELAY":
            color = self.colors[str(os.getenv("NIGHSCOUT_DELAY_COLOR")).upper()]
        else:
            color = self.colors[str(os.getenv("LOW_COLOR")).upper()]
        return color

    def change_1_light(self, color: dict, lightId: int):
        color["on"] = True
        color = json.dumps(color)
        x = requests.put(f"{self.hue_api_link}lights/{lightId}/state", data=color)
        return
    def turn_off_light(self, lightId: int):
        body = json.dumps({"on": False})
        requests.put(f"{self.hue_api_link}lights/{lightId}/state", data=body)


if __name__ == '__main__':
    while True:
        current_time = parser.parse(str(TimeManagement().timezone_converter()[0]))
        try:
            _start_mins_and_secs = [int(x) for x in os.getenv("START_TIME").split(":")]
        except ValueError:
            raise ValueError
        else:
            try:
                _end_mins_and_secs = [int(x) for x in os.getenv("END_TIME").split(":")]
            except ValueError:
                raise ValueError
            else:
                if (datetime.time(hour=int(_end_mins_and_secs[0]), minute=int(_end_mins_and_secs[1]))) < (
                datetime.time(hour=current_time.hour, minute=current_time.minute)) > (
                datetime.time(hour=int(_start_mins_and_secs[0]), minute=int(_start_mins_and_secs[1]))):
                    for i in os.getenv("LIGHT_ID").split(","):
                        HueOperations().turn_off_light(int(i))
                    print("End time has passed, Turning lights off. Lights wont be turned off if they are already off")
                    time.sleep(durations.Duration(os.getenv("REFRESH_RATE")).to_seconds())
                else:
                    now_time = parser.parse(str(TimeManagement().timezone_converter()[0]))
                    nightscout_time = parser.parse(str(TimeManagement().timezone_converter()[1]))
                    difference = now_time - nightscout_time
                    if ((datetime.datetime.min + difference).time()) > datetime.time(
                            minute=int(os.getenv("NIGHTSCOUT_REALTIME_DIFFERENCE"))):
                        print("Nightscout DELAY: Changing to {}".format(str(os.getenv("NIGHSCOUT_DELAY_COLOR").title())))
                        for i in os.getenv("LIGHT_ID").split(","):
                            HueOperations().change_1_light(HueOperations().get_color("DELAY"), int(i))
                        time.sleep(durations.Duration(os.getenv("REFRESH_RATE")).to_seconds())
                    else:
                        if TimeManagement().nightscout_json[0]["sgv"] in range(int(os.getenv("LOW_GLUCOSE_VALUE")), int(
                                os.getenv("HIGH_GLUCOSE_VALUE")) + 1):
                            for i in(os.getenv("LIGHT_ID").split(",")):
                                HueOperations().change_1_light(color=HueOperations().get_color("RANGE"),
                                                               lightId=int(i))
                                print("Glucose IN-RANGE, changing color to {}".format(os.getenv("RANGE_COLOR")))
                            time.sleep(durations.Duration(os.getenv("REFRESH_RATE")).to_seconds())
                        else:
                            if TimeManagement().nightscout_json[0]["sgv"] > int(os.getenv("HIGH_GLUCOSE_VALUE")):
                                for i in (os.getenv("LIGHT_ID").split(",")):
                                    HueOperations().change_1_light(color=HueOperations().get_color("HIGH"),
                                                                   lightId=int(i))
                                    print("HIGH Glucose {1}, changing color to {0}".format(os.getenv("HIGH_COLOR"), TimeManagement().nightscout_json[0]["sgv"]))
                                time.sleep(durations.Duration(os.getenv("REFRESH_RATE")).to_seconds())
                            else:
                                for i in (os.getenv("LIGHT_ID").split(",")):
                                    HueOperations().change_1_light(color=HueOperations().get_color("LOW"),
                                                                   lightId=int(i))
                                    print("LOW Glucose {1}, changing color to {0}".format(os.getenv("LOW_COLOR"), TimeManagement().nightscout_json[0]["sgv"]))
                                time.sleep(durations.Duration(os.getenv("REFRESH_RATE")).to_seconds())