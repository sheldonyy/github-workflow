from my_chrome import MangaCrawler, decrypt_url
import time
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 加密的 URL 和密钥
ENCRYPTED_URL = "êýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔëççåóðóÞææãõêýÝÝÝÔë"
XOR_KEY = "acgn"


def write_to_res(keyword, filepath="res.txt"):
    """单个关键词写入 res.txt（存在记录）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{now} {keyword}\n")


def write_to_fail(keyword, filepath="fail.txt"):
    """单个关键词写入失败列表（需要手动重试）"""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{keyword}\n")


def close_dialog(crawler):
    """关闭弹窗遮罩层（如果存在）"""
    try:
        dialog_btn = crawler.find_element(
            "a.poi-dialog__header__close",
            ".poi-dialog__footer a.poi-dialog__footer__btn.poi-dialog__footer__btn_default",
            "a.poi-dialog__footer__btn_default",
            wait_time=3,
        )
        if dialog_btn:
            crawler.driver.execute_script("arguments[0].click();", dialog_btn)
            time.sleep(0.5)
    except Exception:
        pass  # 没有弹窗就忽略


def click_search_button(crawler, val, attempt, max_retries):
    """点击搜索按钮"""
    search_btn = crawler.find_element("a.inn-search-bar__btn", wait_time=15)
    if search_btn:
        crawler.driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(0.5)
        return True

    print(f"[{val}] 未找到搜索按钮")
    crawler.quit()
    if attempt == max_retries:
        write_to_fail(val)
    return False


def input_search_text(crawler, val, attempt, max_retries):
    """查找输入框并输入内容，回车搜索"""
    search_input = crawler.find_element("input.inn-search-bar__fm__input", wait_time=5)
    if not search_input:
        print(f"[{val}] 未找到搜索输入框")
        crawler.quit()
        if attempt == max_retries:
            write_to_fail(val)
        return False

    search_input.clear()
    search_input.send_keys(val)
    time.sleep(0.3)
    search_input.send_keys(Keys.ENTER)
    time.sleep(3)  # 等待搜索结果页面加载
    return True


def count_search_results(crawler, val):
    """统计搜索结果数量"""
    # 先等待页面加载完成（通过检查某个稳定元素）
    try:
        WebDriverWait(crawler.driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".poi-row, #inn-super-search__container, .inn-search-result")
            )
        )
    except Exception:
        print(f"[{val}] 等待搜索结果区域超时")

    # 尝试多种选择器统计结果
    selectors = [
        "#inn-super-search__container .poi-row article.is-waterfall",
        "#inn-super-search__container article",
        ".poi-row article",
        "article.is-waterfall",
        ".inn-super-search__container article",
    ]

    for selector in selectors:
        try:
            articles = crawler.find_elements(selector, wait_time=5)
            if articles:
                count = len(articles)
                print(f"[{val}] 使用选择器 '{selector}' 找到 {count} 条结果")
                return count
        except Exception:
            continue

    print(f"[{val}] 未找到搜索结果，可能为0条或页面结构变化")
    return 0


def sarch_task(val):
    """单次搜索任务，带重试机制"""
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        crawler = None
        try:
            # 创建爬虫实例（无头模式）
            crawler = MangaCrawler(headless=True)
            # 访问目标页面（使用解密后的 URL）
            target_url = decrypt_url(ENCRYPTED_URL, XOR_KEY)
            crawler.run(target_url)

            # 等待页面加载完成（首次多等一会）
            wait_time = 4 if attempt == 1 else 2
            time.sleep(wait_time)

            # 关闭弹窗遮罩层
            close_dialog(crawler)

            # 点击搜索按钮
            if not click_search_button(crawler, val, attempt, max_retries):
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return -1

            # 输入搜索内容并回车
            if not input_search_text(crawler, val, attempt, max_retries):
                if attempt < max_retries:
                    time.sleep(2)
                    continue
                return -1

            # 统计搜索结果数量
            count = count_search_results(crawler, val)

            # 关闭浏览器
            crawler.quit()
            time.sleep(1)

            # 实时写入结果
            if count == 0:
                write_to_res(val)
                return 0
            return count

        except Exception:
            error_detail = traceback.format_exc()
            print(f"[{val}] 第 {attempt} 次尝试出错:\n{error_detail}")
            if crawler:
                try:
                    crawler.quit()
                except Exception:
                    pass
            if attempt == max_retries:
                write_to_fail(val)
                print(f"[{val}] 已达到最大重试次数，写入失败列表")
                return -1
            time.sleep(3)  # 重试前等待

    return -1


def run_search_tasks(keywords, max_workers=1, progress_callback=None):
    """多线程执行搜索任务

    :param keywords: 搜索关键词列表
    :param max_workers: 最大并发线程数，默认1（避免被封）
    :param progress_callback: 进度回调函数，接收 (current, total, keyword, status, count) 参数
    :return: 字典 {关键词: 结果数量}
    """
    results = {}
    total = len(keywords)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_keyword = {
            executor.submit(sarch_task, keyword): keyword for keyword in keywords
        }
        # 获取结果
        for future in as_completed(future_to_keyword):
            keyword = future_to_keyword[future]
            try:
                count = future.result()
                results[keyword] = count
                status = "成功" if count >= 0 else "失败"
                print(f"[{keyword}] {status}，结果数量: {count}")
            except Exception:
                error_detail = traceback.format_exc()
                results[keyword] = -1
                write_to_fail(keyword)
                print(f"[{keyword}] 线程执行出错:\n{error_detail}")

            completed += 1
            # 调用进度回调
            if progress_callback:
                progress_callback(completed, total, keyword, status if count >= 0 else "失败", count)

    return results
