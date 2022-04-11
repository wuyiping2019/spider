"""
从银保监的官网爬取全部的兼业代理机构的信息
必须选择一项 针对不同的所属地区进行爬取
"""

import requests
import json
from PIL import Image
import pytesseract
import time
import pyodbc
from func_timeout import func_set_timeout
import re
import execjs

"""
获取网页中的《所属地区》的可选值
"""


# 进入主页并保存response和session
def enterHomepage():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Host': 'iir.circ.gov.cn',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }
    time.sleep(3)
    url = 'http://iir.circ.gov.cn/ipq/publicQuery.html'
    session = requests.session()
    time.sleep(1)
    response = session.get(url=url, headers=headers)
    session.cookies.update(response.cookies)
    return session


def getProvinces():
    time.sleep(1)
    response, session = enterHomepage()
    cookies = response.cookies
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Host': 'iir.circ.gov.cn',
        'Referer': 'http://iir.circ.gov.cn/ipq/publicQuery.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    url = 'http://iir.circ.gov.cn/ipq/indusAsscont/provinceList.do'
    provinces = session.get(url=url, cookies=cookies, headers=headers)
    provinces = json.loads(provinces.text)
    provinces = {item['codecname'].replace('银保监局', ''): item['codecode'] for item in provinces}
    session.close()
    return provinces


# 针对区域获取对应的兼业代理机构
def getParttimeInsuranceAgencyByRegion(region):
    # 第一步进入主页
    session = enterHomepage()
    # 第二步获取验证码和cookies
    headers = {
        'Accept': 'image/avif, image/webp, image/apng, image/*, */*;q = 0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Host': 'iir.circ.gov.cn',
        'Proxy-Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
    }
    url = 'http://iir.circ.gov.cn/ipq/captchacn.svl'
    time.sleep(1)
    response = session.get(url=url, headers=headers)
    session.cookies.update(response.cookies)
    with open('./data/yzm.png', 'wb') as f:
        f.write(response.content)
    image = Image.open('./data/yzm.png')
    yzm = re.sub('\s', '', pytesseract.image_to_string(image, lang='eng'))
    # 第三步发送查询请求
    context = execjs.compile("""
        function getDate(){
            return new Date();
        }
    """)
    url = 'http://iir.circ.gov.cn/ipq/intermediary.do?checkcaptch&time=' + context.call('getDate')
    # validstatus:1表示有效 2表示无效
    data = {"agencyname": '', "unifiedcode": '', "agencycode": '', "captcha": yzm,
            "supcode": region, "validstatus": '1'}
    headers.update({'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'})
    response = session.post(url=url, headers=headers, data=data)
    session.cookies.update(response.cookies)
    print(response.text)
    response = session.get('http://iir.circ.gov.cn/ipq/intermediary.html', headers=headers)
    # 第四步进行分页查询
    url = 'http://iir.circ.gov.cn/ipq/intermediary.do?validate'
    response = session.post(url=url)
    url = 'http://iir.circ.gov.cn/ipq/intermediary.do?find'
    data = {
        "page": 1
    }
    session.cookies.update(response.cookies)
    response = session.post(url=url, headers=headers, data=data)
    print(type(response.text))
    print(response.text)
    # 一次返回10条数据 {"queryAllowed":true,"rows":[],"total":4701}
    # 继续发送请求改变page即可
    agencys = json.loads(response.text)
    while True:
        time.sleep(3)
        page = data["page"] + 1
        data.update({"page": page})
        response = session.post(url=url, data=data, headers=headers)
        session.cookies.update(response.cookies)
        temp_agencys = json.loads(response.text)
        if temp_agencys['queryAllowed'] is True and len(temp_agencys['rows']) == 0:
            break
        agencys['rows'] = agencys['rows'] + temp_agencys['rows']
        print(temp_agencys['rows'])
    print(agencys)
    print(len(agencys))
    return agencys


# js_str:js中的函数
# func_name:函数名称
# args:参数列表
def execJs(js_str, func_name, args):
    context = execjs.compile(js_str, func_name)
    date = context.call(func_name, *args)
    return date


if __name__ == '__main__':
    getParttimeInsuranceAgencyByRegion('110000')
