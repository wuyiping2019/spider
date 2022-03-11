import sys
import time
from functools import reduce

from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import re


# 移动滑动条到底部
def scroll2bottom():
    flag = True
    while flag:
        before = driver.find_element(By.XPATH, '//*').get_attribute('outerHTML')
        time.sleep(1)
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        time.sleep(1)
        after = driver.find_element(By.XPATH, '//*').get_attribute('outerHTML')
        if before == after:
            flag = False


def get_total_page(html_str):
    soup = BeautifulSoup(html_str, 'lxml')
    return int(re.sub(r'[^0-9]', '', soup.select_one('.mr20').text))


def parse_html(html_str, f):
    soup = BeautifulSoup(html_str, 'lxml')
    reduce_str = lambda x, y: x + '\t' + y
    reduce_list = lambda x, y: x + '：' + y
    products = soup.select('.prdBlock')
    for product in products:
        inlineBgImage = [product.select_one('.inlineBgImage').text]
        cdleftArea = [reduce(reduce_list, element.text.split('：')[1:]) for element in
                      product.select_one('.cdleftArea').select('.row')]
        cdmidArea = [reduce(reduce_list, element.text.split('：')[1:]) for element in
                     product.select_one('.cdmidArea').select('.row')]
        cdrightArea = [reduce(reduce_list, element.text.split('：')[1:]) for element in
                       product.select_one('.cdrightArea').select('.row')]
        f.write(reduce(reduce_str, (inlineBgImage + cdleftArea + cdmidArea + cdrightArea)) + '\n')


driver = webdriver.Chrome('D:\servers\chromedriver_win32\chromedriver.exe')
driver.maximize_window()
driver.get('http://www.cmbchina.com/cfweb/personal/')
time.sleep(3)
scroll2bottom()
html_str = driver.find_element(By.XPATH, '//*').get_attribute('outerHTML')
total_page = get_total_page(html_str)
f = open('cmb_product.txt', 'w', encoding='utf-8')
for i in range(total_page):
    scroll2bottom()
    driver.find_element(By.XPATH, '//*[@id="tbGoPage"]').send_keys(i + 1)
    time.sleep(1)
    driver.find_element(By.XPATH, '//*[@id="golink"]').click()
    time.sleep(1)
    scroll2bottom()
    html_str = driver.find_element(By.XPATH, '//*').get_attribute('outerHTML')
    parse_html(html_str, f)
f.close()
driver.close()
