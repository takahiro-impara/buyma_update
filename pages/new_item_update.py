import requests
import configparser
import time
import sys
import os
import logging
from logging import getLogger, FileHandler, Formatter, INFO, WARN

import datetime

from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')
from utils.driverOptions import options
from csvs.ReadCsv import CSV

BUYMA_TOP_URL = 'https://www.buyma.com'
LOGIN_URL='https://www.buyma.com/login/'
AUTH_URL='https://www.buyma.com/login/auth/'
BUY_TOP_URL_FORMAT = 'https://www.buyma.com/my/buyeritems/?sro=2&rows=50&p={0}#/'
BUY_SELL_PAGE_FORMAT = 'https://www.buyma.com/my/sell/{0}/edit?tab=b'

config = configparser.ConfigParser()
config.read('../config/config.ini')

logging = getLogger("logger")
logdate_fmt = datetime.datetime.now().strftime('%Y%m%d%H%M')

handler = FileHandler(filename='../log/{0}-buymaupdate.log'.format(logdate_fmt), encoding='utf-8')
handler.setLevel(INFO)
handler.setFormatter(Formatter("%(asctime)s %(levelname)8s %(message)s"))

logging.addHandler(handler)

class ItemUpdate:
    def __init__(self):
        """
        コンストラクタ
        """
        self.session = requests.Session()
        self.account = config['buyma']['account']       
        self.payload = {
            'txtLoginId': config['buyma']['user'],
            'txtLoginPass': config['buyma']['passwd'],
            'login_do': 'ログイン'
        }
    
    def SetLoginSession(self):
        """
        ログインセッションをセットする
        """
        r = self.session.get(LOGIN_URL)
        soup = bs(r.text, 'html.parser')
        onetimeticket = soup.find(attrs={'name': 'onetimeticket'}).get('value')
        self.payload['onetimeticket'] = onetimeticket
        self.session.post(AUTH_URL, data=self.payload)
            
    def open_login_page(self, browser):
        """
        buymaのログインページを開く
        :return: エラーページに遷移した場合はassertion、それ以外はtrue
        """
        print('call open_login_page')
        self.browser = browser
        self.browser.get(LOGIN_URL)

        login_element = self.browser.find_element(By.ID, 'txtLoginId')
        login_element.send_keys(config['buyma']['user'])

        passwd_element = self.browser.find_element(By.ID, 'txtLoginPass')
        passwd_element.send_keys(config['buyma']['passwd'])
        passwd_element.send_keys(Keys.RETURN)

        return True
    
    def open_item_sell_page(self, **kwargs):
        """
        商品更新ページを開く
        :params 
            buyma_id: BUYMA ID
        """
        buyma_id = kwargs['buyma_id']
        print('open {0}'.format(BUY_SELL_PAGE_FORMAT.format(buyma_id)))
        self.browser.get(BUY_SELL_PAGE_FORMAT.format(buyma_id))

    def open_serach_page(self):
        """
        商品検索ページを開く
        """
        SEARCH_URL = 'https://www.buyma.com/my/buyeritems/?ssts=1&tab=b#/'
        self.browser.get(SEARCH_URL)

    def search_item_sell_page(self, **kwargs):
        """
        buyma IDから特定の商品を検索表示する
        buyma_update_data(dict): buyma商品付けデータ
        """
        buyma_num = kwargs['buyma_num']
        print('call search_item_sell_page {0}'.format(buyma_num))
        WebDriverWait(self.browser, 300).until(
                EC.presence_of_element_located((By.ID, 'keyword')))
        search_element = self.browser.find_element(By.ID, 'keyword')
        search_element.clear()
        search_element.send_keys(buyma_num)
        search_element.send_keys(Keys.RETURN)

        if self.is_there_error_inpage():
            return True
        else:
            return False

    def is_there_error_inpage(self):
        """
        表示された画面のエラーを確認する
        """
        html = browser.page_source.encode('utf-8')
        source = bs(html, 'html5lib')
        for error_block in source.find_all('div', class_='error'):
            if '出品アイテムはありません' in error_block.text.strip():
                return True
        return False
    def update_item_size(self, **kwargs):
        """
        表示された商品情報のサイズ情報を更新する
        :param
            buyma_update_data(dict): buyma商品情報
        """
        buyma_update_data=kwargs['buyma_update_data']
        print('call update_item_size {0}'.format(buyma_update_data))
        self.click_size(buyma_update_data['buyma_id'])
        WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'js-colorsize-table-header ')))
                #EC.presence_of_element_located((By.CLASS_NAME, 'jquery-ui-dialog--primary')))

        #更新リストをbuyma情報をベースに作成する
        buyma_update_set = {}
        for buyma_size in buyma_update_data['buyma_sizes'].split(','):
            size = buyma_size.split('/')[0]
            buyma_update_set[size] = '在庫なし'
        
        for key,_ in buyma_update_set.items():
            if key in [x for x in buyma_update_data['total-sizes'].split('/')]:
                buyma_update_set[key] = '買付可'
        del buyma_update_set['']        
        buyma_update_set = self.add_color_size_id(buyma_update_set)
        #全て在庫無しの場合は別の処理を入れる
        if set([x.split('/')[0] for _,x in buyma_update_set.items()]) == {'在庫なし'}:
            #first_size = sorted(buyma_update_set.keys())[0]
            first_size = str(sorted(list(map(float, buyma_update_set.keys())))[0])
            buyma_update_set[first_size] = buyma_update_set[first_size].replace('在庫なし', '買付可')
            self.size_status_modify(buyma_update_set)
            self.click_save()
            self.size_status_modify_no_stock(buyma_update_data)
        else:
            self.size_status_modify(buyma_update_set)
            self.click_save()
            print(buyma_update_data, self.account)
            if buyma_update_data['buyer_name'] != self.account:
                self.price_status_modify(buyma_update_data)

    def click_size(self, buyma_id):
        """
        サイズの「編集」ボタンをクリック
        """
        size_element = self.browser.find_element(By.XPATH, '//a[@data-syo-id={0}]'.format(buyma_id))
        size_element.click()
    
    def click_save(self):
        """
        更新ボタンをクリック
        """
        #debug -> cancelを押下する 要修正
        #save_element = self.browser.find_element_by_link_text('キャンセル')
        save_element = self.browser.find_element_by_link_text('更新する')
        save_element.click()
        time.sleep(0.1)
        html = self.browser.page_source.encode('utf-8')
        source = bs(html, 'html5lib')
        print(source.find('span', class_='js-error-messasge-area').string)
        if source.find('span', class_='js-error-messasge-area').string == '色・サイズ(数量)が変更されていません。':
            #logging.info('[INFO]更新情報なし')
            print('[INFO]更新情報なし')
            _save_element = self.browser.find_element_by_link_text('キャンセル')
            _save_element.click()
    
    def add_color_size_id(self, buyma_update_set):
        """
        colorsize_idを取得する
        """
        _buyma_update_set = buyma_update_set
        html = self.browser.page_source.encode('utf-8')
        source = bs(html, 'html5lib')
        size_color_blocks = source.find_all('tr')
        for size_color_block in size_color_blocks:
            td_blocks = size_color_block.find_all('td')
            try:
                size_text = td_blocks[0].text.strip()
                if td_blocks[0].text.strip() in [x for x,_ in _buyma_update_set.items()]:
                    color_id = str(td_blocks[2].find('select', class_='js-colorsize-select')['colorsizeid'])
                    _buyma_update_set[size_text] += '/' + color_id
            except IndexError:
                continue
            except TypeError:
                continue
        print("color_id")
        print(_buyma_update_set)
        return _buyma_update_set
    def size_status_modify(self, buyma_update_set):
        """
        各サイズの情報を修正する
        :params
            buyma_update_set: buyma更新データ
        """
        print(buyma_update_set)
        for size, is_stock in buyma_update_set.items():
            is_there_stock, color_id = is_stock.split('/')
            color_xpath = "//select[@colorsizeid={0}]".format(color_id)
            element  = self.browser.find_element_by_xpath(color_xpath)
            element.click()

            size_xpath = "//select[@colorsizeid={0}]/option[text()=\"{1}\"]".format(color_id, is_there_stock)
            element  = self.browser.find_element_by_xpath(size_xpath)
            element.click()

    def size_status_modify_no_stock(self, buyma_update_data):
        """
        全てのサイズで在庫が無い場合、仮で在庫ありとした最初のサイズを在庫なしとして更新する
        """
        buyma_update_data = buyma_update_data
        self.browser.get(BUY_SELL_PAGE_FORMAT.format(buyma_update_data['buyma_id']))
        WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'sell-status-switch')))
        self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        switch_element  = self.browser.find_element_by_class_name('sell-status-switch')
        switch_element.click()
        self.click_save_btn()
        self.open_serach_page()

    def click_save_btn(self):
        """
        在庫無しの場合の更新情報保存ボタンをクリック
        """
        WebDriverWait(self.browser, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'bmm-c-btn--thick'))) 
        save_element  = self.browser.find_element_by_class_name('bmm-c-btn--thick')
        save_element.click()
        WebDriverWait(self.browser, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'sell-complete__ttl'))) 
    
    def price_status_modify(self, buyma_update_data):
        """
         販売情報を修正する
        :params
            buyma_update_set: buyma更新データ       
        """
        buyma_update_data=buyma_update_data
        print('call update_price {0}'.format(buyma_update_data))
        self.click_price(buyma_update_data['buyma_id'])
        WebDriverWait(self.browser, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'js-item-price'))) 
        price_input_element = self.browser.find_element_by_name('item_price')
        price_input_element.clear()
        price_input_element.send_keys(str(buyma_update_data['change_price']))
        time.sleep(1)
        self.save_price()
        time.sleep(1)

    def click_price(self, buyma_id):
        """
        価格の「編集」ボタンをクリック
        """
        size_element = self.browser.find_element(By.CLASS_NAME, '_item_edit_tanka')
        size_element.click()
    
    def save_price(self):
        """
        価格の「設定する」ボタンをクリック
        """
        size_element = self.browser.find_element(By.LINK_TEXT, '設定する')
        size_element.click()       

if __name__ == '__main__':
    all_item_url = []
    all_item_info = []
    driver_path = '../resource/chromedriver'
#    input_file = '../input/buyma_link.csv'
    input_file = '../input/tmp.csv'

    buyma = ItemUpdate()
    buyma.SetLoginSession() 
    
    buyma_update_datas = CSV().GetDictFromCsv(input_file)
    options = Options()
    browser = webdriver.Chrome(chrome_options=options, executable_path=driver_path)
    buyma.open_login_page(browser)
    buyma.open_serach_page()
    logging.info('ツール実行開始')
    for buyma_update_data in buyma_update_datas:
        try:
            is_there_error = buyma.search_item_sell_page(buyma_num=buyma_update_data['buyma_num'])
            if is_there_error:
                print('[ERROR] 商品情報が見つかりません {0}'.format(buyma_update_data))
                #logging.info('[ERROR] 商品情報が見つかりません {0}'.format(buyma_update_data))
                continue
            elif buyma_update_data['item_num'] == 'NotFound':
                print('[INFO] 引当たりなしのため、出品停止処理を開始します {0}'.format(buyma_update_data))
                #logging.info('[INFO] 引当たりなしのため、出品停止処理を開始します {0}'.format(buyma_update_data))
                buyma.size_status_modify_no_stock(buyma_update_data)

            else:
                print('[INFO] 商品登録情報の修正を実施します {0}'.format(buyma_update_data))
                #logging.info('[INFO] 商品登録情報の修正を実施します {0}'.format(buyma_update_data))
                buyma.update_item_size(buyma_update_data=buyma_update_data)
                print('[OK]商品情報登録: {0}'.format(buyma_update_data))
                #logging.info('[OK]商品情報登録: {0}'.format(buyma_update_data))
        except Exception as e:
            print('buyma商品情報の更新に失敗しました {0}'.format(e))
            print(buyma_update_data)
            #logging.info('[NG]buyma商品情報の更新に失敗しました {0}:{1}'.format(e, buyma_update_data))
            continue
    
    browser.quit()
    print('ツール実行終了')
    #logging.info('ツール実行終了')
