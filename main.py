import http.client
import json

# query for input data
# create cluster for descriptor
# parse output data format

accesstoken = ''

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
            'date': list_item['date']
            # 'mediaType': list_item['mediaType'],
            # 'vendor': list_item['vendor'],
            # 'type': list_item['type'],
            # 'presentation': list_item['presentation'],
        }
        if 'description' in list_item:
            result_item['description'] = list_item['description']

        if 'show' in list_item:
            result_item['show_id'] = list_item['show']['id']
            result_item['show_title'] = list_item['show']['title']
            result_item['show_description'] = list_item['show']['description']
            # result_item['show_vendor'] = list_item['show']['vendor']
            # result_item['show_transmission'] = list_item['show']['transmission']

        if 'episode' in list_item:
            result_item['episode_id'] = list_item['episode']['id']
            result_item['episode_title'] = list_item['episode']['title']
            if 'description' in list_item['episode']:
                result_item['episode_description'] = list_item['episode']['description']
            result_item['episode_publishedDate'] = list_item['episode']['publishedDate']

        result.append(result_item)
    return result


def get_episode_metadata(episode_id, business_unit):
    path = "/videometadata/v2/latest_episodes/shows/{}?bu= {}".format(episode_id, business_unit)
    print(path)
    data = http_request(path)
    print(data)

def get_media_metadata(media_id, business_unit):
    path = "/videometadata/v2/{}/mediaComposition?bu={}".format(media_id, business_unit)
    print(path)
    data = http_request(path)
    print(data)

if __name__ == '__main__':
    data = get_video_data_by_date('2021-03-20', 'srf')
    for element in data:

