import http.client

# query for input data
# create cluster for descriptor
# parse output data format



def get_video_data_by_date(date, business_unit):

    # create request
    payload = ""
    path = "/videometadata/v2/episodes_by_date/{}/?bu= {}&pageSize={}".format(date, business_unit, 100)
    headers = {'accept': "application/json"}

    # request data
    connection = http.client.HTTPSConnection("api.srgssr.ch")
    connection.request("GET", path, payload, headers)
    response = connection.getresponse()

    # process response
    data = response.read()
    print(data.decode("utf-8"))


def get_episode_metadata(episode_id, business_unit):

    # create request
    payload = ""
    path = "/videometadata/v2/latest_episodes/shows/{}/?bu= {}".format(episode_id, business_unit)
    headers = {'accept': "application/json"}

    # request data
    connection = http.client.HTTPSConnection("api.srgssr.ch")
    connection.request("GET", path, payload, headers)
    response = connection.getresponse()

    # process response
    data = response.read()
    print(data.decode("utf-8"))

def get_media_metadata(media_id, business_unit):

    # create request
    payload = ""
    path = "/videometadata/v2/{}/mediaComposition?bu={}".format(media_id, business_unit)
    headers = {'accept': "application/json"}

    # request data
    connection = http.client.HTTPSConnection("api.srgssr.ch")
    connection.request("GET", path, payload, headers)
    response = connection.getresponse()

    # process response
    data = response.read()
    print(data.decode("utf-8"))
