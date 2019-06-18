import tweepy
import json
import re
from dotenv import load_dotenv
from pathlib import Path
from os import environ as e
import regex
import pandas as pd

class Tweet:
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    def __init__(self, *args):
        self.consumer_key = e['CONSUMER_KEY']
        self.consumer_secret = e['CONSUMER_SECRET']
        self.access_token = e['ACCESS_TOKEN']
        self.access_token_secret = e['ACCESS_TOKEN_SECRET']

    def authenticate(self):
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(self.access_token, self.access_token_secret)
        api = tweepy.API(auth, wait_on_rate_limit = True)
        self.api = api
    
    def get_tweet(self, url):
        ms = re.match(r'https:\/\/twitter.com\/(\w+)\/status\/(\d+)', url)
        screen_name = ms.group(1)
        tweet_id = ms.group(2)
        self.screen_name = screen_name
        self.tweet_id = tweet_id

    def get_replies(self,since_day, until_day):
        results = [reply._json['full_text'] for reply in tweepy.Cursor(self.api.search, q='@{}'.format(self.screen_name), \
            result_type = 'recent', \
            since_id = self.tweet_id, \
            lang = 'ja', \
            rpp = 100, \
            count = 200, \
            tweet_mode = 'extended', \
            since = since_day, \
            until = until_day
            ).items(1000)]
        return results
    
    def format_tweet(self, results):
        targets = [' '.join(result.replace('\u3000', ' ').replace('\n', ' ').replace('／', '/').replace('(', '').replace(')', '').split()) for result in results if re.findall(r'(\d+(\/|\／)\d+)', result)]
        formatted_list = [' '.join(re.sub(r'(.*)(@[a-zA-Z0-9_]{1,15})', '',target).split()) for target in targets]
        short_lst = []
        for formatted in formatted_list:
            short_lst += regex.findall(r'([\p{Hiragana}\p{Katakana}\p{Han}]+\s*\d+\/\d+)', formatted)
        return short_lst

    def create_counter(self):
        members = [
                    ['小坂菜緒', '小坂', '菜緒', 'こさかな'], 
                    ['齊藤京子', '齊藤', '京子', 'きょんこ'], 
                    ['加藤史帆', '加藤', '史帆', 'としちゃん'], 
                    ['河田陽菜', '河田', '陽菜', 'かわださん'], 
                    ['上村ひなの', '上村', 'ひなの'], 
                    ['東村芽依', '東村', '芽依'], 
                    ['高本彩花', '高本', '彩花', 'おたけ'],
                    ['宮田愛萌', '宮田', '愛萌', 'まなも'],
                    ['高瀬愛奈', '高瀬', '愛奈', 'まなふぃ'],
                    ['富田鈴花', '富田', '鈴花', 'すずか'],
                    ['潮紗理菜', '潮', '紗理菜', 'なっちょ'],
                    ['佐々木久美', '佐々木', '久美', 'くみ', 'ささく'],
                    ['井口眞緒', '井口', '眞緒'],
                    ['濱岸ひより', '濱岸', 'ひより']
                    ]
        member_list = [member[0] for member in members]
        count = [0] * len(members)
        winning_counter = dict(zip(member_list, count))
        application_counter = dict(zip(member_list, count))
        return members, winning_counter, application_counter

    def count_by_member(self, members, winning_counter, application_counter ,short_lst):
        difficult_lst = []
        easy_lst = []

        for member in members:
            for member_name in member:
                for short in short_lst:
                    re_lst = regex.match(r'([\p{Hiragana}\p{Katakana}\p{Han}]+)\s*(\d+)\/(\d+)', short)
                    if re_lst.group(1) == member_name:
                        easy_lst.append(short)
                        winning_counter[member[0]] += int(re_lst.group(2))
                        application_counter[member[0]] += int(re_lst.group(3))

        difficult_lst = list(filter(lambda x: x not in easy_lst, short_lst))
        return difficult_lst, winning_counter, application_counter

    def insert_csv(self, difficult_lst, winning_counter, application_counter):
        df = pd.io.json.json_normalize(winning_counter).T
        df.rename(columns={0: '当選数'}, inplace=True)
        df['申込数']= pd.io.json.json_normalize(application_counter).T
        df['当選確率']= df['当選数'] / df['申込数'] * 100
        df.to_csv('自動集計.csv', encoding='shift_jis')
        df1 = pd.DataFrame(difficult_lst, columns=['未集計'])
        df1.to_csv('手動集計.csv', encoding='shift_jis')

if __name__ == '__main__':
    tweet = Tweet()
    api = tweet.authenticate()
    tweet.get_tweet('https://twitter.com/Hinatazaka46PR/status/1139523903041048578')
    results = tweet.get_replies(since_day='2019-06-14', until_day='2019-06-18')
    short_lst = tweet.format_tweet(results=results)
    members, winning_counter, application_counter = tweet.create_counter()
    difficult_lst, winning_counter, application_counter = tweet.count_by_member(members=members, winning_counter=winning_counter, application_counter=application_counter ,short_lst=short_lst)
    tweet.insert_csv(difficult_lst=difficult_lst, winning_counter=winning_counter, application_counter=application_counter)
    