import pickle

class Cookie:
    def __init__(self, browser):
        browser
        if 'Style' in browser.title:
            self.cookie_path = '../cookies/cookies-{0}.pkl'.format('styleisnow')
        elif 'lidiashopping' in browser.title:
            self.cookie_path = '../cookies/cookies-{0}.pkl'.format('lidiashopping')



    def saveCookie(self, browser):
        """
        Cookieの保存
        :return: cookie object
        """
        self.browser = browser
        pickle.dump(self.browser.get_cookies(), open(self.cookie_path, "wb"))

        return True

    def addCookie(self, browser):
        """
        Cookieを読み込み
        :param url: 同一ドメインのURL
        :return:
        """
        self.browser = browser
        cookies = pickle.load(open(self.cookie_path, "rb"))
        for cookie in cookies:
            self.browser.add_cookie(cookie)

        return self.browser