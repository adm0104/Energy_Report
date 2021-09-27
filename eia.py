import requests
import pandas as pd

class weeklyReport:
    #   Class to store weekly report data. Input "seriesNames" from "seriesQuery" helper function
    #   is pre-populated with the API calls needed to pull the data included in the EIA's weekly energy report.
    #   Uses the helper function "seriesQuery" below.
    #   Inputs:
    #       apiKeyLocation:         String
    #           File path (as a string) for a .txt document containing an EIA API key
    #           EXAMPLE: 'C:\User\key.txt'
    def __init__(self, apiKeyLocation):
        seriesNames = {
            'PET.WCRSTUS1.W': 'Crude Oil',
            'PET.WCESTUS1.W': 'Crude Oil Excl. SPR',
            'PET.WCSSTUS1.W': 'Crude Oil SPR',
            'PET.WGTSTUS1.W': 'Total Gasoline',
            'PET.WGRSTUS1.W': 'Reformulated Gasoline',
            'PET.WG4ST_NUS_1.W': 'Conventional Gasoline',
            'PET.WBCSTUS1.W': 'Blending Components',
            'PET.W_EPOOXE_SAE_NUS_MBBL.W': 'Fuel Ethanol',
            'PET.WKJSTUS1.W': 'Kerosene-Type Jet Fuel',
            'PET.WDISTUS1.W': 'Distillate Fuel Oil',
            'PET.WD0ST_NUS_1.W': 'Distillate 0 to 15 ppm sulfur',
            'PET.WD1ST_NUS_1.W': 'Distillate 15 to 500 ppm sulfur',
            'PET.WDGSTUS1.W': 'Distillate 500+ ppm sulfur',
            'PET.WRESTUS1.W': 'Residual Fuel Oil',
            'PET.WPRSTUS1.W': 'Propane/Propylene Excl. Terminal',
            'PET.W_EPPO6_SAE_NUS_MBBL.W': 'Other Oils',
            'PET.WUOSTUS1.W': 'Unfinished Oils',
            'PET.WTTSTUS1.W': 'Total Stocks Incl. SPR',
            'PET.WTESTUS1.W': 'Total Stocks Excl. SPR'
        }
        self.timeSeries, self.header = seriesQuery(seriesNames, apiKeyLocation)

def seriesQuery(seriesNames, apiKeyLocation):
    #   Used to query the Energy Information Administration (EIA) API for any weekly data series.
    #   Inputs:
    #       seriesNames:        List or Dict
    #           If list, should include API series ID's for each desired element
    #           EXAMPLE: seriesNames = ['PET.WCESTUS1.W']
    #           If dict, should include API series ID's as dict keys, and series nicknames as dict elements (1 per key)
    #           EXAMPLE: seriesNames = {'PET.WCESTUS1.W': 'Commercial Crude Oil'}
    #       apiKeyLocation:     String
    #           File path (as a string) for a .txt document containing an EIA API key
    #           EXAMPLE: 'C:\User\key.txt'
    #   Outputs:
    #       timeSeries:         Pandas DataFrame
    #           Combined timeseries data from each series requested through EIA API
    #           Data will be indexed by the data collection date (per EIA weekly report), NOT reporting date
    #           With list input for seriesNames, columns will be named after series ID's
    #           With dict input for seriesNames, columns will be named after column nicknames
    #       metaData:           Pandas DataFrame
    #           Includes all header data from API response, 1 row per requested series

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