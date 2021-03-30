import numpy as np
import pandas as pd
import nltk
import re
import os
import codecs
import mpld3
import http.client
import json
import os  # for os.path.basename

import matplotlib.pyplot as plt
import matplotlib as mpl

from sklearn.manifold import MDS

from sklearn import feature_extraction
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

accesstoken = ''
business_unit = 'srf' # srf, rtr, rts, rsi
num_clusters = 10

ignore_shows = (
    '32a8a665-e50d-4622-a4ec-3a99aba0a731', # Wetterkanal
    ''
)

stemmer = SnowballStemmer("german")

def http_request(path):
    # create request
    payload = ""
    headers = {'accept': "application/json", 'Authorization': 'Bearer {}'.format(accesstoken)}

    # request data
    connection = http.client.HTTPSConnection("api.srgssr.ch")
    connection.request("GET", path, payload, headers)
    response = connection.getresponse()

    # process response
    data = json.loads(response.read())
    return data


"""
queries the online service for each date individually to gather shows that ran on these dates.
we only need the show_ids since the rest of the information should be available 
"""
def get_video_data_by_date(date, business_unit):
    path = "/videometadata/v2/episodes_by_date/{}?bu={}&pageSize={}".format(date, business_unit, 25)
    print(path)
    data = http_request(path)

    if 'next' in data:
        # TODO: recursive add next page items.
        print("next page detected for date {}".format(date))

    result = []

    for list_item in data['mediaList']:
        # pick only the relevant information

        title = list_item['title']
        if title.lower().startswith(("wetterkanal", "tagesschau", "meteo", "10")):
            continue

        result_item = {
            'id': list_item['id'],
            'title': list_item['title'],
#            'date': list_item['date']
            # 'mediaType': list_item['mediaType'],
            # 'vendor': list_item['vendor'],
            # 'type': list_item['type'],
            # 'presentation': list_item['presentation'],
        }

        print(result_item)
#        if 'description' in list_item:
#            result_item['description'] = list_item['description']

        if 'show' in list_item:
            result_item['show_id'] = list_item['show']['id']
            result_item['show_title'] = list_item['show']['title']
            if 'description' in list_item['show']:
                result_item['show_description'] = list_item['show']['description']
            # result_item['show_vendor'] = list_item['show']['vendor']
            # result_item['show_transmission'] = list_item['show']['transmission']
        else:
            print("WARNING: no show found in element {} ({})!".format(result_item['id'], result_item['title']))

#        if 'episode' in list_item:
#            result_item['episode_id'] = list_item['episode']['id']
#            result_item['episode_title'] = list_item['episode']['title']
#            if 'description' in list_item['episode']:
#                result_item['episode_description'] = list_item['episode']['description']
#            result_item['episode_publishedDate'] = list_item['episode']['publishedDate']

        result.append(result_item)
    return result


"""
query for the show metadata, specifically for the metadata to each episode that this show has.
"""
def get_show_metadata(episode_id, business_unit):
    path = "/videometadata/v2/latest_episodes/shows/{}?bu={}&pageSize={}".format(episode_id, business_unit, 3)
    data = http_request(path)

    if 'next' in data:
        # TODO: recursive add next page items.
        print("next page detected for episode {}".format(episode_id))

    # get general show data:
    show_data = {
        'id': data['show']['id'],
        'vendor': data['show']['vendor'],
        'title': data['show']['title'],
    }
    if 'description' in data['show']:
        show_data['description'] = data['show']['description']
    if 'lead' in data['show']:
        show_data['lead']: data['show']['lead']

    medias = []
    episodes = []
    if 'episodeList' in data:
        for list_item in data['episodeList']:
            episode_item = {
                'id': list_item['id'],
                'title': list_item['title'],
                'show': show_data
            }
            if 'description' in list_item:
                episode_item['description'] = list_item['description']
            if 'lead' in list_item:
                episode_item['lead'] = list_item['lead']
            if 'socialCount' in list_item and list_item['socialCount']['key'] == 'srgviews':
                episode_item['srgviews']: list_item['socialCount']['value']

            for media_list_item in list_item['mediaList']:
                media_element = {
                    'id': media_list_item['id'],
                    'episode_id': episode_item['id'],
                    'title': media_list_item['title']
                }
                if 'description' in media_list_item:
                    media_element['description'] = media_list_item['description']
                if 'lead' in media_list_item:
                    element['lead'] = media_list_item['lead']
                medias.append(media_element)

            episodes.append(episode_item)

    return episodes, medias


"""
query for additional information such as likes, clicks, and shares"""
def get_media_metadata(media_id, business_unit):
    path = "/videometadata/v2/{}/mediaComposition?bu={}".format(media_id, business_unit)
    print(path)
    data = http_request(path)
    print(data)

def tokenize_and_stem(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word for sent in nltk.sent_tokenize(text, language="german") for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    stems = [stemmer.stem(t) for t in filtered_tokens]
    return stems


def tokenize_only(text):
    # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
    tokens = [word.lower() for sent in nltk.sent_tokenize(text, language="german") for word in nltk.word_tokenize(sent)]
    filtered_tokens = []
    # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
    for token in tokens:
        if re.search('[a-zA-Z]', token):
            filtered_tokens.append(token)
    return filtered_tokens


if __name__ == '__main__':
    # TODO: this currently only queries for one day as seed, but we would like to have an iterator over the last n days.
    show_data = get_video_data_by_date('2021-03-25', business_unit)

    episode_data = []
    media_data = []

    for element in show_data:
        episodes, medias = get_show_metadata(element['show_id'], business_unit)
        episode_data.extend(episodes)
        media_data.extend(medias)

    episode_ids = []
    episode_texts = []

    for element in episode_data:

        element_id = element['title']

        element_text = ""

        if 'lead' in element:
            element_text += element['lead']
        elif 'description' in element:
            element_text += element['description']
        if len(element_text) == 0:
            element_text = element['show']['description']

        episode_ids.append(element_id)
        episode_texts.append(element_text)

    vocab_stemmed = []
    vocab_tokenized = []
    for element in episode_texts:
        vocab_stemmed.extend(tokenize_and_stem(element))
        vocab_tokenized.extend(tokenize_only(element))

    vocab_frame = pd.DataFrame({'words': vocab_tokenized}, index=vocab_stemmed)
    print('there are ' + str(vocab_frame.shape[0]) + ' items in vocab_frame')

    stopwords = nltk.corpus.stopwords.words('german')
    print(stopwords)
    stopwords_stemmed = []
    for element in stopwords:
        stopwords_stemmed.extend(tokenize_and_stem(element))

    tfidf_vectorizer = TfidfVectorizer(max_df=0.8, max_features=200000, min_df=0.1, use_idf=True,
                                       tokenizer=tokenize_and_stem, ngram_range=(1, 3), stop_words=stopwords_stemmed)
    tfidf_matrix = tfidf_vectorizer.fit_transform(episode_texts)  # fit the vectorizer to synopses

    terms = tfidf_vectorizer.get_feature_names()
    dist = 1 - cosine_similarity(tfidf_matrix)

    km = KMeans(n_clusters=num_clusters)
    km.fit(tfidf_matrix)
    clusters = km.labels_.tolist()

    cluster_episode = {'id': episode_ids, 'text': episode_texts, 'cluster': clusters}

    frame = pd.DataFrame(cluster_episode, index = [clusters] , columns = ['id', 'text', 'cluster'])
    frame['cluster'].value_counts()

    grouped = frame['id'].groupby(frame['cluster'])

    # sort cluster centers by proximity to centroid
    order_centroids = km.cluster_centers_.argsort()[:, ::-1]

    for i in range(num_clusters):
        print("Cluster %d words:" % i, end='')

        for ind in order_centroids[i, :6]:  # replace 6 with n words per cluster
            print(' %s' % vocab_frame.loc[terms[ind].split(' ')].values.tolist()[0][0].encode('utf-8', 'ignore'),
                  end=',')
        print("Cluster %d text:" % i, end='')
        for title in frame.loc[i]['id'].values.tolist():
            print(' %s,' % title, end='')

    MDS()

    # convert two components as we're plotting points in a two-dimensional plane
    # "precomputed" because we provide a distance matrix
    # we will also specify `random_state` so the plot is reproducible.
    mds = MDS(n_components=2, dissimilarity="precomputed", random_state=1)

    pos = mds.fit_transform(dist)  # shape (n_components, n_samples)

    xs, ys = pos[:, 0], pos[:, 1]

    # set up colors per clusters using a dict
    cluster_colors = {0: '#006400', 1: '#00008b', 2: '#b03060', 3: '#ff4500', 4: '#ffd700', 5: '#7fff00', 6: '#00ffff', 7: '#ff00ff', 8: '#6495ed', 9: '#ffdab9'}

    # set up cluster names using a dict
    cluster_names = {0: '1',
                     1: '2',
                     2: '3',
                     3: '4',
                     4: '5',
                     5: '6',
                     6: '7',
                     7: '8',
                     8: '9',
                     9: '10'
                     }

    # create data frame that has the result of the MDS plus the cluster numbers and titles
    df = pd.DataFrame(dict(x=xs, y=ys, label=clusters, title=episode_ids))

    # group by cluster
    groups = df.groupby('label')

    # set up plot
    fig, ax = plt.subplots(figsize=(17, 9))  # set size
    ax.margins(0.05)  # Optional, just adds 5% padding to the autoscaling

    # iterate through groups to layer the plot
    # note that I use the cluster_name and cluster_color dicts with the 'name' lookup to return the appropriate color/label
    for name, group in groups:
        ax.plot(group.x, group.y, marker='o', linestyle='', ms=12,
                label=cluster_names[name], color=cluster_colors[name],
                mec='none')
        ax.set_aspect('auto')
        ax.tick_params( \
            axis='x',  # changes apply to the x-axis
            which='both',  # both major and minor ticks are affected
            bottom='off',  # ticks along the bottom edge are off
            top='off',  # ticks along the top edge are off
            labelbottom='off')
        ax.tick_params( \
            axis='y',  # changes apply to the y-axis
            which='both',  # both major and minor ticks are affected
            left='off',  # ticks along the bottom edge are off
            top='off',  # ticks along the top edge are off
            labelleft='off')

    ax.legend(numpoints=1)  # show legend with only 1 point

    # add label in x,y position with the label as the film title
    for i in range(len(df)):
        ax.text(df.loc[i]['x'], df.loc[i]['y'], df.loc[i]['title'], size=8)

    plt.show()

    plt.close()

    for i in range(1, len(episode_data)):
        episode_data[i]['cluster_id'] = clusters[i]

    print(episode_data)