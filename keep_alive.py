import requests
import time

while True:
    try:
        requests.get("https://special-winner-rjrgvg6q96j25q4r.github.dev/")
        time.sleep(300)  # هر 5 دقیقه پینگ بزند
    except:
        pass