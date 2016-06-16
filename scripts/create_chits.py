import time
import requests

jokes = json.load(open('jokes.json'))['value']
r = redis.StrictRedis(host="localhost", port=6379, db=0)


def main():
    for jokeitem in jokes:
        r.hset(app.CHITTER_H, str(joke.id), json.dumps({
            "date": time.time(),
            "id": "{}")


if __name__ == "__main__":
    main()
