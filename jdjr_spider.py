import json
import os.path
import re
import requests
import datetime
# 京东金融财富榜 持仓百万大佬都在买/赚钱人数基金榜/金牛奖基金蝉联榜/新手热销榜
# 榜单 基金编码 产品id 产品名称 近一年利率 截止日期 购买人数 排名
# 京东金融财富榜 热门板块
# 板块名称 板块编码 昨日收盘点 近期趋势x轴、y轴数据、成交量、涨幅、最高、最低、开盘价、换手率、板块名称、市盈率、收盘价
# 京东金融财富榜 低估指数榜
# 指数编号、指数名称、排名、pe、pe百分位、pb、pb百分位、roe、日涨幅、周涨幅、月涨幅、半年涨幅、年涨幅

def create_sql(item: dict, table_name: str):
    fields = ''
    values = ''
    for kv in item.items():
        fields += kv[0] + ', '
        values += "'" + str(kv[1]).replace("'", "''") + "', "
    fields = '(' + fields.rstrip(', ') + ')'
    values = '(' + values.rstrip(', ') + ')'
    sql = f'''insert into {table_name}{fields} values{values};'''
    sql = (re.sub(r"\s+", " ", sql) + '\n')  # .replace("'","''")
    return sql


path = 'create_sql.sql'
if os.path.exists(path):
    os.remove(path)

print("-----------------------持仓百万大佬都在买/赚钱人数基金榜/金牛奖基金蝉联榜/新手热销榜 开始-----------------")
url = 'https://ms.jr.jd.com/gw/generic/base/h5/m/execute1'
dataTemplate = {
    'reqData': '{"deviceId":"fund_business_query_stock","version":"201","searchSource":2,"paramMap":{"rank_type":"{rank_type}","appKey":"uop.jd.com","appSecret":"60e10537-5457-4743-8a1c-6187079e8936","pageNum":"1"}}'
}
rankTypeDict = {
    'earn': '持仓百万大佬都在买',
    'rich': '赚钱人数基金榜',
    'jinNiu': '金牛奖基金蝉联榜',
    'greenHands': '新手热销榜'
}
f = open('create_sql.sql', 'a', encoding='UTF-8')
f.write("-------------持仓百万大佬都在买/赚钱人数基金榜/金牛奖基金蝉联榜/新手热销榜 开始" + '\n')
for rank_type in 'earn', 'rich', 'jinNiu', 'greenHands':
    data = {}
    data['reqData'] = dataTemplate['reqData'].replace('{rank_type}', rank_type)
    resp = requests.post(url=url, data=data)
    parsed_resp = json.loads(resp.text)
    for item in parsed_resp['resultData']['data']:
        item['rank_type'] = rankTypeDict[rank_type]
        item['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(create_sql(item, 'jdjr_rank_type'))
f.write("-------------持仓百万大佬都在买/赚钱人数基金榜/金牛奖基金蝉联榜/新手热销榜 结束" + '\n')
f.close()
print("-----------------------持仓百万大佬都在买/赚钱人数基金榜/金牛奖基金蝉联榜/新手热销榜 结束-----------------")

print("-----------------------热门板块 开始-----------------")
f = open('create_sql.sql', 'a', encoding='UTF-8')
f.write("-------------热门板块 开始" + '\n')
url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/hotPlateList'
plateName2plateCode = {}
resp = requests.get(url=url)
parsed_resp = json.loads(resp.text)['resultData']['data']['list']
for hot_product in parsed_resp:
    plateName2plateCode[hot_product['plateInfo']['plateName']] = hot_product['plateInfo']['plateCode']
    hot_product_platInfo = hot_product['plateInfo']
    hot_product_platInfo['platePointList'] = hot_product['marketTrendChart']['platePointList']
    hot_product_platInfo['xList'] = [int(item) for item in hot_product['marketTrendChart']['xList']]
    hot_product_platInfo['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(create_sql(hot_product_platInfo, 'jdjr_hotproduct_platInfo'))
f.write("-------------热门板块 结束" + '\n')
f.close()
print("-----------------------热门板块 结束-----------------")

print("-----------------------热门板块具体板块 开始-----------------")
f = open('create_sql.sql', 'a', encoding='UTF-8')
f.write("-------------热门板块具体板块 开始" + '\n')
print('plateName2plateCode:', plateName2plateCode)
url = 'https://ms.jr.jd.com/gw/generic/uc/h5/m/hotPlateTrendChart'
dataTemplate = {'reqData': '{"timeDimension": {timeDimension}, "plateCode": "{plateCode}", "stockIndex": 1}'}
timeDimensionDesc = {
    1: '实时',
    2: '近1月',
    3: '近3月',
    4: '近6月',
    5: '近1年',
    6: '今年'
}
# 遍历不同的热门板块产品
for item in plateName2plateCode.items():
    plateName = item[0]
    plateCode = item[1]
    data = {}
    data['reqData'] = dataTemplate['reqData'].replace('{plateCode}', str(plateCode))
    # 遍历不同的时间范围
    flag = True  # 在查询某个板块的数据时,遍历不同时间范围过程中板块最上面的数据是不变的,使用该flag标识仅记录一次
    for timeDimension in sorted(timeDimensionDesc.keys()):
        data['reqData'] = data['reqData'].replace('{timeDimension}', str(timeDimension))
        resp = requests.post(url=url, data=data)
        parsed_resp = json.loads(resp.text)
        if flag:
            marketInfo = parsed_resp['resultData']['data']['marketInfo']
            marketInfo['plateName'] = plateName
            marketInfo['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(create_sql(marketInfo, 'jdjr_hotplate_marketInfo'))
            flag = False
        fundList = parsed_resp['resultData']['data']['fundList']
        for fund in fundList:
            fund['plateName'] = plateName
            fund['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fund['timeDimension'] = timeDimensionDesc[timeDimension]
            f.write(create_sql(fund, 'hotplate_fund'))
        marketTrendChart = parsed_resp['resultData']['data']['marketTrendChart']
        marketTrendChart['plateName'] = plateName
        marketTrendChart['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        marketTrendChart['timeDimention'] = timeDimensionDesc[timeDimension]
        f.write(create_sql(marketTrendChart, 'hotplate_marketTrendChart'))
f.write("-------------热门板块具体板块 结束" + '\n')
f.close()
print("-----------------------热门板块具体板块 结束-----------------")

print("-----------------------跟热点 重仓茅台十大基金榜 开始-----------------")
f = open('create_sql.sql', 'a', encoding='UTF-8')
url = 'https://ms.jr.jd.com/gw/generic/starlink/h5/m/execute/user_wealth'
data = {'reqData': '{"flowKey":"F600241415450222110929992","params":{"stockCode":"600519"}}'}
resp = requests.post(url=url, data=data)
parsed_resp = json.loads(resp.text)
fundInfoList = parsed_resp['resultData']['data']['fundInfoList']
f.write('-------------插入跟热点->重仓茅台十大基金榜的数据 开始' + '\n')
for fundInfo in fundInfoList:
    fundInfo['stockCode'] = parsed_resp['resultData']['data']['stockCode']
    fundInfo['stockName'] = parsed_resp['resultData']['data']['stockName']
    f.write(create_sql(fundInfo, 'heavy_warehouse_maotai'))
f.write('-------------插入跟热点->重仓茅台十大基金榜的数据 完毕' + '\n')
f.close()
print("-----------------------跟热点 重仓茅台十大基金榜 结束-----------------")
print("-----------------------避风险 精选固收 开始-----------------")
f = open('create_sql.sql', 'a', encoding='UTF-8')
url = 'https://ms.jr.jd.com/gw/generic/starlink/h5/m/execute/user_wealth'
data = {'reqData': '{"flowKey":"F111280303120316170625218"}'}
resp = requests.post(url=url, data=data)
parsed_resp = json.loads(resp.text)
fundInfoList = parsed_resp['resultData']['data']['fundInfoList']
f.write('-------------避风险 精选固收 开始' + '\n')
for fundInfo in fundInfoList:
    fundInfo['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    f.write(create_sql(fundInfo, 'avoid_risk_choiceness'))
f.write('-------------避风险 精选固收 结束' + '\n')
f.close()
print("-----------------------避风险 精选固收 结束-----------------")

print("-----------------------抗跌牛基榜/盈利潜力榜 开始-----------------")
f = open('create_sql.sql', 'a', encoding='UTF-8')
url = 'https://ms.jr.jd.com/gw/generic/jj/h5/m/getFundChannelPageRankingList'
dataTemplate = {'reqData': '{"pageNo":1,"pageSize":10,"rankingType":{rankingType},"itemLabel":{itemLabel}}'}
rankingTypeDesc = {
    1: '抗跌牛基榜',
    2: '盈利潜力榜'
}
itemLabelDesc = {
    1: '进取收益',
    2: '安心稳健',
    2: '布局海外'
}


def process_data(dataTemplate, rankingType, itemLabel):
    data = {}
    data['reqData'] = dataTemplate['reqData'].replace('{rankingType}', str(rankingType)).replace('{itemLabel}',
                                                                                                 str(itemLabel))
    return data


def process_result(result):
    for item in result.items():
        key = item[0]
        value = item[1]
        if isinstance(value, dict):
            result[key] = result[key]['text']
    return result


f.write('-------------抗跌牛基榜/盈利潜力榜 开始' + '\n')
for rankingType in rankingTypeDesc.items():
    rankingType_key = rankingType[0]
    rankingType_value = rankingType[1]
    for itemLabel in itemLabelDesc.items():
        itemLabel_key = itemLabel[0]
        itemLabel_value = itemLabel[1]
        data = process_data(dataTemplate, rankingType_key, itemLabel_key)
        resp = requests.post(url=url, data=data)
        parsed_resp = json.loads(resp.text)
        resultData = parsed_resp['resultData']['resultData']
        for result in resultData:
            result = process_result(result)
            result['list'] = rankingType_value
            result['desc'] = itemLabel_value
            f.write(create_sql(result, 'ldnjb_and_ylqlb'))
f.write('-------------抗跌牛基榜/盈利潜力榜 结束' + '\n')
f.close()
print("-----------------------抗跌牛基榜/盈利潜力榜 结束-----------------")

print("-----------------------指数涨跌榜 开始-----------------")
f = open('create_sql.sql', 'a', encoding='UTF-8')
f.write('-------------指数涨跌榜 开始' + '\n')
url = 'https://ms.jr.jd.com/gw/generic/jrm/h5/m/indexChartList'
dataTemplate = {
    'reqData': '{"clientType":"other","clientVersion":"","req":{"sortType":"raisePercent1W","sort":1,"type":"{type}","pageSize":20,"pageNo":1}}'}
for i in range(4):
    type = i + 1
    data = {}
    data['reqData'] = dataTemplate['reqData'].replace('{type}', str(i + 1))
    resp = requests.post(url=url, data=data)
    parsed_resp = json.loads(resp.text)
    for i in range(len(parsed_resp['resultData']['data']['list'])):
        typeData = parsed_resp['resultData']['data']['list'][i]
        typeDesc = typeData['typeDesc']
        dataList = typeData['dataList']
        columnNameList = [item['columnValue'] for item in typeData['columnList']]
        for data in dataList:
            data_processed = {}
            data_processed['stockName'] = data['stockName']
            data_processed['viewCode'] = data['viewCode']
            data_processed['stockCode'] = data['stockCode']
            data_processed['jumpInfo_p'] = data['jumpInfo']['p']
            data_processed['jumpInfo_t'] = data['jumpInfo']['t']
            data_processed['typeDesc'] = typeDesc
            columnData = data['columnData']
            for column_data, column_name in zip(columnData, columnNameList):
                data_processed[column_name] = column_data
            f.write(create_sql(data_processed, 'index_up_and_fall'))
f.write('-------------指数涨跌榜 结束' + '\n')
f.close()
print("-----------------------指数涨跌榜 结束-----------------")

print("-----------------------低估指数榜 开始-----------------")
url = 'https://ms.jr.jd.com/gw/generic/jrm/h5/m/getUnderrateIndexChart'
data = {
    'reqData': '{"clientType":"other","clientVersion":"","req":{"sortType":"null","sort":-1,"pageSize":10,"pageNo":1}}'
}
resp = requests.post(url=url, data=data)
parsed_resp = json.loads(resp.text)
dataList = parsed_resp['resultData']['data']['dataList']
columnList = parsed_resp['resultData']['data']['columnList']
updateTime = parsed_resp['resultData']['data']['updateTime']
columnList_value = [item['columnValue'] for item in columnList]
f = open('create_sql.sql', 'a', encoding='UTF-8')
f.write('-------------低估指数榜 开始' + '\n')
for dataListItem in dataList:
    processed_data = {}
    processed_data['uCode'] = dataListItem['uCode']
    processed_data['appraisementStatus'] = dataListItem['appraisementStatus']
    processed_data['stockName'] = dataListItem['stockName']
    processed_data['viewCode'] = dataListItem['viewCode']
    processed_data['jumpInfo_p'] = dataListItem['jumpInfo']['p']
    processed_data['jumpInfo_t'] = dataListItem['jumpInfo']['t']
    for i, j in zip(dataListItem['columnData'], columnList_value):
        processed_data[j] = i
    processed_data['updateTime'] = updateTime
    processed_data['infoTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    processed_data['topic'] = '低估指数榜'
    f.write(create_sql(processed_data, 'under_evaluation_index'))
f.write('-------------低估指数榜 结束' + '\n')
f.close()
print("-----------------------低估指数榜 结束-----------------")
