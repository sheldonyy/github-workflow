from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import os


import base64


def decrypt_url(encrypted_url):
    """Base64 解码"""
    return base64.b64decode(encrypted_url).decode('utf-8')


def encrypt_url(url):
    """Base64 编码"""
    return base64.b64encode(url.encode('utf-8')).decode('utf-8')


class MangaCrawler:
    def __init__(self, headless=False, device_mode=''):
        self.options = Options()
        self._set_base_options()
        if headless:
            self._set_headless_mode()
        # 设备模式配置
        if device_mode == "mobile":
            mobile_emulation = {
                "deviceMetrics": {"width": 375, "height": 812, "pixelRatio": 3.0},
                "userAgent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
            }
            self.options.add_experimental_option("mobileEmulation", mobile_emulation)
        elif device_mode == "desktop":
            # 桌面模式配置
            pass
        elif device_mode == "tablet":
            # 平板模式配置
            pass
        elif isinstance(device_mode, dict) and device_mode != '':
            # 传入自定义配置
            self.options.add_experimental_option("mobileEmulation", device_mode)
        
        self.service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(
            service=self.service, 
            options=self.options,
        )
        # 隐式等待 10 秒（对所有 find_element 生效）
        self.driver.implicitly_wait(10) 
        
    def _set_base_options(self):
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option("useAutomationExtension", False)
        self.options.add_argument('--log-level=3')  # 只显示 FATAL 错误
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")

    def _set_headless_mode(self):
        self.options.add_argument("--headless=new")


    def find_element(self, kwargs, wait_time = 0, mode=By.CSS_SELECTOR):
        """查找单个元素
        :param kwargs: CSS 选择器
        :param wait_time: 等待时间，单位为秒
        :return: 元素对象
        """
        try:
            if wait_time > 0:
                return WebDriverWait(self.driver, wait_time).until(EC.presence_of_element_located((mode, kwargs)))
            else:
                return self.driver.find_element(mode, kwargs)
        except Exception as e:
            print(f"查找元素时发生意外错误: {str(e)}")
        return None
        
    def find_elements(self, kwargs, wait_time = 0):
        """查找多个元素
        :param kwargs: CSS 选择器
        :param wait_time: 等待时间，单位为秒
        :return: 元素列表
        """
        if wait_time > 0:
            return WebDriverWait(self.driver, wait_time).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, kwargs)))
        else:
            return self.driver.find_elements(By.CSS_SELECTOR, kwargs)
        
    def getImgBase64(self, url):
        return self.driver.execute_script("""
            const url = arguments[0];
            return new Promise((resolve, reject) => {
                fetch(url)
                .then(response => response.blob())
                .then(blob => {
                    const reader = new FileReader();
                    reader.readAsDataURL(blob); 
                    reader.onloadend = () => {
                    const base64data = reader.result;
                    resolve(base64data); // 通过 Promise resolve 返回
                    };
                    reader.onerror = () => {
                    reject("读取失败");
                    };
                })
                .catch(error => {
                    reject("下载失败: " + error);
                });
            });
        """, url)

    def run(self, url):
        # 配置国内镜像加速
        os.environ['WDM_HTTPPROXY'] = "https://npm.taobao.org/mirrors/chromedriver"
        os.environ['WDM_LOCAL'] = "./drivers"
        
        try:
            # print(f"正在访问: {url}")
            self.driver.get(url)

        except Exception as e:
            print(f"运行过程中出错: {str(e)}")
        # finally:
        #     print("关闭浏览器...")
        #     self.driver.quit()
    def quit(self):
        self.driver.quit()

if __name__ == "__main__":
    crawler = MangaCrawler(headless=False)
    crawler.run("https://www.douyin.com/user/MS4wLjABAAAApSowZfWOVMCGZQETtqrFKjTSTCjsQ7odxklU01rLMCk?from_tab_name=main&vid=7494815920503590182")
    # 定义方法


