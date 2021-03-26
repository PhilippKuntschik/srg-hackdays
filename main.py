import numpy as np
import pandas as pd
import nltk
import re
import os
import codecs
from sklearn import feature_extraction
import mpld3
import http.client
import json

# query for input data
# create cluster for descriptor
# parse output data format

accesstoken = 'LUQt20DQQsBGm9SiI6clRiCuTPG2'
business_unit = 'srf' # srf, rtr, rts, rsi

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
    path = "/videometadata/v2/episodes_by_date/{}?bu={}&pageSize={}".format(date, business_unit, 100)
    print(path)
    data = http_request(path)

    if 'next' in data:
        # TODO: recursive add next page items.
        print("next page detected for date {}".format(date))

    result = []

    for list_item in data['mediaList']:
        # pick only the relevant information

        result_item = {
            'id': list_item['id'],
            'title': list_item['title'],
#            'date': list_item['date']
            # 'mediaType': list_item['mediaType'],
            # 'vendor': list_item['vendor'],
            # 'type': list_item['type'],
            # 'presentation': list_item['presentation'],
        }
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


if __name__ == '__main__':
    # TODO: this currently only queries for one day as seed, but we would like to have an iterator over the last n days.
    show_data = get_video_data_by_date('2021-03-20', business_unit)

    episode_data = []
    media_data = []

    for element in show_data:
        episodes, medias = get_show_metadata(element['show_id'], business_unit)
        episode_data.extend(episodes)
        media_data.extend(medias)

    to_cluster = ()
    for media in media_data:
        cluster_input = {'id': media['id']}
        cluster_input['text']: media['description']
        to_cluster.append(cluster_input)