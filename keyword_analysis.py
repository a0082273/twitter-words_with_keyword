import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import MeCab
import re
from collections import Counter
from wordcloud import WordCloud

keyword_list = [
                # 'sumou',
                # 'tsururyuu', 'shiroootori', 'mareseinosato', 'kusamafuji',
                # 'goueidou', 'takayasu', 'tochinokokoro',
                # 'ontakeumi', 'tamawashi', 'matsuootoriyama',
                # 'shoudai', 'konshoukiku', 'chiyonokuni', 'ahonoo', 'takashikeishou', 'kaihijiri',
                # 'daishoumaru', 'kakaze', 'chiyodairyuu', 'takarafuji', 'daieishou',
                # 'chiyoshouuma', 'asahidaihoshi', 'myougiryuu', 'yutakayama', 'chiyomaru',
                # 'nishikiki', 'hekiyama', 'abusaki', 'sadanoumi', 'kouwashi', 'tochikouyama',
                # 'asanoyama', 'konmegumihikari', 'okinoumi', 'ishiura', 'ryuuden',
                # 'kitakachifuji', 'akiumi', 'hattorisakura',
                # '#sumo', '#sumou', '#oozumou', '#nagoyabasho',
                 'ena', 'nakatsugawa', 'tajimi', 'mizunami',
]


for i in range(len(keyword_list)):
    keyword = keyword_list[i]
    period = '2018-07-18' #edit!!!!!!!!!
    infile = "tweets_in_a_week/keyword/"+keyword+period+".csv" #edit!!!!!!!!!
    outfile = "tweets_in_a_week/keyword/"+keyword+period+".png"
    datas = pd.read_csv(open(infile, 'rU'), encoding='utf-8')


    datas = datas.drop('Unnamed: 0', axis=1)
    improper_col = []
    for col in range(datas.shape[0]):
        if type(datas.text[col]) != str:
            print('-'*40)
            print('nan in text: keyword={}, col={}'.format(keyword, col))
            improper_col.append(col)
        # elif type(datas.name[col]) != str:
        #     datas.name[col] = 'nan_name'
        # elif type(datas.profile[col]) != str:
        #     datas.profile[col] = 'nan_profile'
    datas = datas.drop(improper_col, axis=0)
    datas = datas.reset_index(drop=True)

    datas['n_following'] = datas['n_following'].astype('int')
    datas['n_followed'] = datas['n_followed'].astype('int')
    datas['n_tweets'] = datas['n_tweets'].astype('int')
    datas['n_favorited'] = datas['n_favorited'].astype('int')

    improper_names  = ['bot', 'Bot', 'BOT', 'ぼっと', '情報', '案内', '相互', '出会', 'セフレ', 'エッチ', '法人',
                       '相撲 バズウォール', '逢華', '大西啓太', #for sumou
    ]
    improper_profiles  = ['improper_words', 'bot', 'Bot', 'BOT', 'ぼっと',
    ]
    improper_texts  = ['improper_words', "I'm at", '相互',
                       '火ノ丸', '大喜利', '手押し相撲' , '一人相撲' , '独り相撲', 'ローション', '名言集', '紙相撲', #for sumou
                       '火の丸', 'カーネーション', '他人の褌で相撲を取る', '菊とギロチン', '伝令', '尻相撲',
                       '格闘技、プロ野球、相撲好き', '女相撲一座とアナキスト'#for sumou
    ]

    for col in range(datas.shape[0]):
        if type(datas['name'][col]) == str:
            for word in improper_names:
                if word in datas['name'][col]:
                    datas.loc['profile', col] = 'improper_words'
                    break
        if type(datas['profile'][col]) == str:
            for word in improper_profiles:
                if word in datas['profile'][col]:
                    datas.loc['text', col] = 'improper_words'
                    break
        for word in improper_texts:
            if word in datas['text'][col]:
                datas = datas.drop(col, axis=0)
                break

    datas = datas.reset_index(drop=True)




    m = MeCab.Tagger("-d /usr/local/lib/mecab/dic/mecab-ipadic-neologd/")
    word_list = []
    for i in range(datas.shape[0]):
        if type(datas.text[i]) == str:
            texts = m.parse(datas['text'][i])
            texts = texts.split('\n')
            for text in texts:
                text = re.split('[\t,]', text)
                if text[0] == 'EOS' or text[0] == '':
                    pass
                elif text[1] == '名詞':
                    word_list.append(text[0])

    stop_words = ['in', 'ー', 'bot', 'https', 'co', 'ない', '無い', '投稿', 'ツイート', '今日', '明日', '昨日', '今週', '来週', '先週',
                  '相撲', '名古屋場所', 'sumo', 'さん', 'こと', '場所', '大相撲', 'よう', '力士', '中継', 'それ', 'どこ',
                  'NHK', 'これ', 'みたい', '名前', '自分', '相撲部', 'ちゃん', '相撲取り', '大相撲名古屋場所', 'そう',
                  '相手', '土俵', '登録', 'くん', 'あと', 'そこ', 'ため', 'うち', 'ここ', 'ところ', 'なん', '感じ',
                  'もの', 'とき', 'やつ', 'もん', 'しよう', 'わけ', 'たち', 'とこ', 'つもり', 'こちら', '？？？', 'あれ',
                  'しんみ', 'した', 'せい', 'さま', 'さっき', 'こっち', 'かな', 'まま', '最近', '時間', 'みんな']

    def remove_specified_values(arr, value):
        while value in arr:
            arr.remove(value)

    for word in stop_words:
        remove_specified_values(word_list, word)

    counter = Counter(word_list)

    word_list = ' '.join(word_list)


    fpath = "~/Library/Fonts/RictyDiminished-Regular.ttf"

    wordcloud = WordCloud(background_color="white", font_path=fpath, width=900, height=500, max_words=80).generate(word_list)

    plt.figure(figsize=(10,8))
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.savefig(outfile)
    plt.close()
#    plt.show()
