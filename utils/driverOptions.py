from selenium.webdriver.chrome.options import Options

options = Options()
# ヘッダレスモードを有効化する（コメントアウトするとブラウザが表示される）
options.add_argument("--headless")
options.add_argument("--disable-gpu")
#options.add_argument("--window-size=1280x1696")
options.add_argument("--window-size=1920,1920")
options.add_argument('--dns-prefetch-disable')
options.add_argument("--disable-application-cache")
options.add_argument("--disable-infobars")
options.add_argument("--no-sandbox")
options.add_argument("--hide-scrollbars")
options.add_argument("--enable-logging")
options.add_argument("--log-level=0")
options.add_argument("--single-process")
options.add_argument("--ignore-certificate-errors")
options.add_experimental_option("prefs", {
  "download.default_directory":'../outputs/',
})
