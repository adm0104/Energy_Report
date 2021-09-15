import requests
import pandas as pd

def seriesQuery(seriesNames, apiKeyLocation):

    if isinstance(seriesNames, dict):
        queryList = list(seriesNames.keys())
        nickNames = pd.DataFrame.from_dict(seriesNames, orient = 'index', columns = ['nickName'])
    elif isinstance(seriesNames, list):
        queryList = seriesNames

    with open(apiKeyLocation) as f:
        key = f.readlines()[0]

    url = 'http://api.eia.gov/series/?api_key=' + key + '&series_id=' + queryList[0]
    data = requests.get(url).json()
    timeSeries = pd.DataFrame(data['series'][0].pop('data'), columns = ['rawDate', data['series'][0]['series_id']])
    metaData = pd.DataFrame(data['series'])

    for i in queryList[1:]:
        url = 'http://api.eia.gov/series/?api_key=' + key + '&series_id=' + i
        data = requests.get(url).json()
        timeStore = pd.DataFrame(data['series'][0].pop('data'), columns = ['rawDate', data['series'][0]['series_id']])
        timeSeries = timeSeries.merge(timeStore)
        metaData = metaData.append(pd.DataFrame(data['series']), ignore_index = True)

    metaData = metaData.set_index('series_id')

    if isinstance(seriesNames, dict):
        timeSeries.rename(columns = seriesNames, inplace = True)
        metaData['series_id'] = metaData.index
        metaData = metaData.join(nickNames).set_index('nickName')

    year = timeSeries['rawDate'].str[:4].astype(int)
    month = timeSeries['rawDate'].str[4:6].astype(int)
    day = timeSeries['rawDate'].str[6:8].astype(int)
    timeSeries['reportDate'] = pd.to_datetime([f'{y}-{m}-{d}' for y, m, d in zip(year, month, day)])
    timeSeries = timeSeries.set_index('reportDate')
    timeSeries.pop('rawDate')

    return timeSeries, metaData