# -*- coding: utf-8 -*-

from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys
from abc import ABCMeta, abstractmethod
import csv
import pandas as pd
from pykakasi import kakasi
import os
from os.path import join, dirname
from dotenv import load_dotenv


dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)
CK= os.environ.get("CK")
CS= os.environ.get("CS")
AT= os.environ.get("AT")
AS= os.environ.get("AS")


class TweetsGetter(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        self.session = OAuth1Session(CK, CS, AT, AS)

    @abstractmethod
    def specifyUrlAndParams(self, keyword):
        '''
        呼出し先 URL、パラメータを返す
        '''

    @abstractmethod
    def pickupTweet(self, res_text, includeRetweet):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''

    @abstractmethod
    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''

    def collect(self, total = -1, onlyText = False, includeRetweet = False):
        '''
        ツイート取得を開始する
        '''

        #----------------
        # 回数制限を確認
        #----------------
        self.checkLimit()

        #----------------
        # URL、パラメータ
        #----------------
        url, params = self.specifyUrlAndParams()
        params['include_rts'] = str(includeRetweet).lower()
        # include_rts は statuses/user_timeline のパラメータ。search/tweets には無効

        #----------------
        # ツイート取得
        #----------------
        cnt = 0
        unavailableCnt = 0
        while True:
            res = self.session.get(url, params = params)
            if res.status_code == 503:
                # 503 : Service Unavailable
                if unavailableCnt > 10:
                    raise Exception('Twitter API error %d' % res.status_code)

                unavailableCnt += 1
                print ('Service Unavailable 503')
                self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
                continue

            unavailableCnt = 0

            if res.status_code != 200:
                raise Exception('Twitter API error %d' % res.status_code)

            tweets = self.pickupTweet(json.loads(res.text))
            if len(tweets) == 0:
                # len(tweets) != params['count'] としたいが
                # count は最大値らしいので判定に使えない。
                # ⇒  "== 0" にする
                # https://dev.twitter.com/discussions/7513
                break

            for tweet in tweets:
                if (('retweeted_status' in tweet) and (includeRetweet is False)):
                    pass
                else:
                    if onlyText is True:
                        yield tweet['text']
                    else:
                        yield tweet

                    cnt += 1
                    if cnt % 100 == 0:
                        print ('%d件 ' % cnt)

                    if total > 0 and cnt >= total:
                        return

            params['max_id'] = tweet['id'] - 1

            # ヘッダ確認 （回数制限）
            # X-Rate-Limit-Remaining が入ってないことが稀にあるのでチェック
            if ('X-Rate-Limit-Remaining' in res.headers and 'X-Rate-Limit-Reset' in res.headers):
                if (int(res.headers['X-Rate-Limit-Remaining']) == 0):
                    self.waitUntilReset(int(res.headers['X-Rate-Limit-Reset']))
                    self.checkLimit()
            else:
                print ('not found  -  X-Rate-Limit-Remaining or X-Rate-Limit-Reset')
                self.checkLimit()

    def checkLimit(self):
        '''
        回数制限を問合せ、アクセス可能になるまで wait する
        '''
        unavailableCnt = 0
        while True:
            url = "https://api.twitter.com/1.1/application/rate_limit_status.json"
            res = self.session.get(url)

            if res.status_code == 503:
                # 503 : Service Unavailable
                if unavailableCnt > 10:
                    raise Exception('Twitter API error %d' % res.status_code)

                unavailableCnt += 1
                print ('Service Unavailable 503')
                self.waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
                continue

            unavailableCnt = 0

            if res.status_code != 200:
                raise Exception('Twitter API error %d' % res.status_code)

            remaining, reset = self.getLimitContext(json.loads(res.text))
            if (remaining == 0):
                self.waitUntilReset(reset)
            else:
                break

    def waitUntilReset(self, reset):
        '''
        reset 時刻まで sleep
        '''
        seconds = reset - time.mktime(datetime.datetime.now().timetuple())
        seconds = max(seconds, 0)
        print ('\n     =====================')
        print ('     == waiting %d sec ==' % seconds)
        print ('     =====================')
        sys.stdout.flush()
        time.sleep(seconds + 10)  # 念のため + 10 秒

    @staticmethod
    def bySearch(keyword):
        return TweetsGetterBySearch(keyword)


class TweetsGetterBySearch(TweetsGetter):
    '''
    キーワードでツイートを検索
    '''
    def __init__(self, keyword):
        super(TweetsGetterBySearch, self).__init__()
        self.keyword = keyword

    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/search/tweets.json'
#        params = {'q':'exclude:retweets', 'geocode':self.keyword, 'count':100}
        params = {'q':'', 'geocode':self.keyword, 'count':100}
        return url, params

    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text['statuses']:
            results.append(tweet)

        return results

    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['search']['/search/tweets']['remaining']
        reset     = res_text['resources']['search']['/search/tweets']['reset']

        return int(remaining), int(reset)



if __name__ == '__main__':
    kakasi = kakasi()
    kakasi.setMode('H', 'a')
    kakasi.setMode('K', 'a')
    kakasi.setMode('J', 'a')
    conv = kakasi.getConverter()

    location_dict = {'yamaoka': '35.329932,137.355972,5km', #山岡町全体
                     'iwamura': '35.359858,137.438441,4km', #岩村町全体
                     'okute': '35.439830,137.296237,3km', #大湫町
#station
                     'nakatsugawa': '35.50009,137.502939,3km', #中津川駅中心に3km
                     'ena': '35.455031,137.40803,3km', #恵那駅
                     'mizunami': '35.369016,137.252072,3km', #瑞浪駅
                     'tokishi': '35.359764,137.182195,3km', #土岐市
                     'tajimi': '35.334979,137.121042,3km', #多治見
                     'kozoji': '35.264438,137.043071,3km', #高蔵寺
                     'kasugai': '35.243034,136.98509,3km', #春日井
                     'kachigawa': '35.229857,136.956302,3km', #勝川
                     'ozone': '35.191489,136.936846,3km', #大曽根
                     'chikusa': '35.170167,136.930662,3km', #千種
                     'tsurumai': '35.156389,136.917527,3km', #鶴舞
                     'kanayama': '35.143045,136.900905,3km', #金山
                     'nagoya': '35.171348,136.883000,3km', #名古屋駅
#
                     'aichiken_taikukan': '35.183071,136.902576,0.2km'} #大相撲名古屋場所
    location = list(location_dict.keys())[-1]   #edit!!!!!!!!!!!!!!!!!!!!!!!!!!
    location_geo = list(location_dict.values())[-1]   #edit!!!!!!!!!!!!!!!!!!!!!!!!!!
    since = '2018-07-08'   #edit!!!!!!!!!!!!!!!!!!!!!!!!!!
    until = '2018-07-09'   #edit!!!!!!!!!!!!!!!!!!!!!!!!!!

    getter = TweetsGetter.bySearch(location_geo+' since:'+since+' until:'+until)

    df = pd.DataFrame(columns=["time", "id", "name", "profile", "n_following",
                               "n_followed", "n_tweets", "adress", "n_favorited","text"])
    for tweet in getter.collect(total = 30000):
        date_time = (tweet["created_at"])
        id = (tweet["user"]["screen_name"])
        name = (tweet["user"]["name"])
        profile = (tweet["user"]["description"])
        n_following = (tweet["user"]["friends_count"])
        n_followed = (tweet["user"]["followers_count"])
        n_tweets = (tweet["user"]["statuses_count"])
        addres = (tweet["user"]["location"])
        n_favorited = (tweet["favorite_count"])
        text = (tweet["text"])

        new_col = pd.Series([date_time, id, name, profile, n_following,
                             n_followed, n_tweets, addres, n_favorited, text],
                            index=["time", "id", "name", "profile", "n_following",
                                   "n_followed", "n_tweets", "adress", "n_favorited","text"])

        df = df.append(new_col, ignore_index=True)

#    df.to_csv('tweets_in_a_week/geocode/'+location+since+'.csv')   #edit!!!!!!!!!!!!!!!!!!!!!!!!!!
    df.to_csv('tweets_in_a_day/geocode/'+location+since+'.csv')
