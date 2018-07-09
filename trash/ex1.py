# -*- coding: utf-8 -*-

from requests_oauthlib import OAuth1Session
import json
import datetime, time, sys

CK = '3ZNIhrv2S6unYYS212eCT2OzF'                             # Consumer Key
CS = 'IHui5X0OMae6r6GuBsAlqqAnr2tua9FHtDFxXIKr2BuUwnvXzI'    # Consumer Secret
AT = '1010769007-BU1MG4dDxcTmBmG1saENkfPcDqFGDAemqETuUI3'    # Access Token
AS = 'b9rC3W8LlNQrvrNKkSdlVNHrYcfFsQ1q47AhhD9A63h5T'         # Accesss Token Secert

session = OAuth1Session(CK, CS, AT, AS)

url = 'https://api.twitter.com/1.1/search/tweets.json'
res = session.get(url, params = {'q':u'瑞浪', 'count':10})

#--------------------
# ステータスコード確認
#--------------------
if res.status_code != 200:
    print ("Twitter API Error: %d" % res.status_code)
    sys.exit(1)

#--------------
# ヘッダー部
#--------------
print ('アクセス可能回数 %s' % res.headers['X-Rate-Limit-Remaining'])
print ('リセット時間 %s' % res.headers['X-Rate-Limit-Reset'])
sec = int(res.headers['X-Rate-Limit-Reset'])\
           - time.mktime(datetime.datetime.now().timetuple())
print ('リセット時間 （残り秒数に換算） %s' % sec)

#--------------
# テキスト部
#--------------
res_text = json.loads(res.text)
for tweet in res_text['statuses']:
    print ('-----')
    print (tweet['created_at'])
    print (tweet['text'])
