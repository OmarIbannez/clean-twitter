import tweepy
import pandas as pd
import argparse
import sys
from tweepy.error import TweepError

CONSUMER_KEY = ""
CONSUMER_SECRET = ""
ACCESS_TOKEN = ""
ACCESS_TOKEN_SECRET = ""
USERNAME = ""
LIMIT = 3200


def argument_parser():
    parser = argparse.ArgumentParser(description="Clean your twitter account.")
    parser.add_argument(
        "-w", "--words", nargs="*", help="List of comma separated words."
    )
    parser.add_argument(
        "-s", "--show", action="store_true", help="Only show the tweets."
    )
    parser.add_argument(
        "-n",
        "--nuke",
        action="store_true",
        help="Delete all tweets that match the words list.",
    )
    parser.add_argument(
        "-dt", "--delete-tweets", action="store_true", help="Delete tweets."
    )
    parser.add_argument(
        "-dr", "--delete-retweets", action="store_true", help="Delete retweets."
    )
    parser.add_argument(
        "-t", "--tweets-ids", nargs="+", help="List of comma tweet IDs."
    )
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()


def get_api(consumer_key, consumer_secret, access_token, access_token_secret):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)


def get_tweets_data_frame(api, username, limit):
    cursor = tweepy.Cursor(api.user_timeline, id=username, include_rts=True)
    data = [
        [tweet.id, tweet.created_at, tweet.retweeted, tweet.text]
        for tweet in cursor.items(limit)
    ]
    return pd.DataFrame(data, columns=["id", "created_at", "retweeted", "text"])


def filter_data_frame(df, words):
    return df[df["text"].str.contains("|".join(words), case=False)]


def delete_tweet(api, tweet_id):
    try:
        api.destroy_status(tweet_id)
    except TweepError:
        pass


def unretweet(api, tweet_id):
    try:
        api.unretweet(tweet_id)
    except TweepError:
        pass


def nuke(api, username, words, limit):
    df = get_tweets_data_frame(api, username, limit)
    fdf = filter_data_frame(df, words)
    for index, row in fdf.iterrows():
        if row.retweeted:
            unretweet(api, row.id)
        else:
            delete_tweet(api, row.id)
    return fdf


if __name__ == "__main__":
    args = argument_parser()
    api = get_api(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    if args.words and args.show:
        df = get_tweets_data_frame(api, USERNAME, LIMIT)
        fdf = filter_data_frame(df, args.words)
        print("The following tweets were found:")
        print(fdf)

    if args.words and args.nuke:
        print("Deleting tweets... 😬")
        df = nuke(api, USERNAME, args.words, LIMIT)
        print("The following tweets were deleted: 🎉")
        print(df)

    if args.delete_tweets and not args.tweets_ids:
        print("You need to provide a list of tweets IDs.")
    if args.delete_tweets and args.tweets_ids:
        print("Deleting tweets... 😬")
        for tweet_id in args.tweets_ids:
            delete_tweet(api, tweet_id)
        print("Done 🎉")

    if args.delete_retweets and not args.tweets_ids:
        print("You need to provide a list of retweets IDs.")
    if args.delete_retweets and args.tweets_ids:
        print("Deleting retweets... 😬")
        for tweet_id in args.tweets_ids:
            unretweet(api, tweet_id)
        print("Done 🎉")
