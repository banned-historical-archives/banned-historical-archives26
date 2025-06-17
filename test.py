import requests
import tempfile
import sys
import json
import hashlib
from urllib.parse import urlparse
import os
from bs4 import BeautifulSoup
import time

# 设置请求头，模拟浏览器访问
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

local_socks5_proxy = os.environ.get('HTTP_PROXY')
proxy=local_socks5_proxy # 传入代理
# 配置代理
proxies = {
    'http': proxy,
    'https': proxy
} if proxy else None
def fetch_wikileaks_search_results_with_proxy(query, exact_phrase, start_page, end_page, document_date_end=None):
    """
    抓取维基解密搜索结果，支持使用代理，并使用新的CSS选择器。

    Args:
        query (str): 搜索关键词。
        start_page (int): 起始页码。
        end_page (int): 结束页码。
        document_date_end (str, optional): 文档结束日期，格式YYYY-MM-DD。默认为 None。
        proxy (str, optional): SOCKS5代理地址，例如 'socks5h://localhost:11999'。默认为 None。

    Returns:
        list: 包含所有抓取到的搜索结果的列表。
    """
    base_url = "https://search.wikileaks.org/advanced"

    for page in range(start_page, end_page + 1):
        params = {
            "any_of": "",
            "page": page,
            "exact_phrase": exact_phrase,
            "query": query,
            "released_date_end": "",
            "document_date_start": "",
            "order_by": "most_relevant",
            "released_date_start": "",
            "new_search": "True",
            "exclude_words": "",
        }
        if document_date_end:
            params["document_date_end"] = document_date_end

        print(f"正在抓取第 {page} 页 (通过代理: {proxy if proxy else '无'})...")
        try:
            # 发送请求时传入proxies和headers参数

            md5_hash = hashlib.md5((base_url + json.dumps(params)).encode('utf-8')).hexdigest()

            html_list_name = os.path.join(os.getcwd(), 'html_list', md5_hash[:4], md5_hash + '.html')

            response_text = ''
            if os.path.exists(html_list_name):
                print('ignore', md5_hash)
                with open(html_list_name, 'r', encoding='utf-8') as file:
                    response_text = file.read()
            else:
                response = requests.get(base_url, params=params, proxies=proxies, headers=headers, timeout=10)
                response.raise_for_status()  # 检查HTTP请求是否成功
                response_text = response.text
                if not os.path.exists(os.path.dirname(html_list_name)):
                    os.makedirs(os.path.dirname(html_list_name))
                safe_write(html_list_name, response_text)

            soup = BeautifulSoup(response_text, 'html.parser')

            # --- 关键修改：根据新的选择器 '.result .info a' 来查找元素 ---
            # 首先找到所有 class 为 'result' 的 div
            results_containers = soup.find_all('div', class_='result')

            if not results_containers:
                print(f"第 {page} 页没有找到搜索结果容器（.result），可能已到达最后一页或页面结构改变。")
                break

            total = 0
            for container in results_containers:
                # 在每个 .result 容器内查找 .info 元素
                info_div = container.find('div', class_='info')
                if info_div:
                    # 在 .info 元素内查找 <a> 标签，这将是标题和链接
                    title_link_tag = info_div.find('a')
                    link = title_link_tag['href'] if title_link_tag else "N/A"
                    total += 1

                    fetch_detail(link)
            if total == 0:
                sys.exit()
            #time.sleep(2)  # 礼貌性延迟，避免给服务器造成过大压力

        except requests.exceptions.ProxyError as e:
            print(f"代理连接错误，请检查代理设置和网络连接: {e}")
            break # 代理错误则停止
        except requests.exceptions.RequestException as e:
            print(f"请求第 {page} 页时发生错误: {e}。状态码：{response.status_code if 'response' in locals() else '未知'}")
            break # 出现其他请求错误则停止抓取
        except Exception as e:
            print(f"解析第 {page} 页时发生错误: {e}")
            break

def safe_write(f, c):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as temp_f:
        temp_f.write(c)
        temp_f.flush()
        os.fsync(temp_f.fileno()) 

    temp_file_path = temp_f.name
    os.replace(temp_file_path, f)

def fetch_detail(link):
    fname = hashlib.md5(link.encode('utf-8')).hexdigest()
    directory = os.path.join(os.getcwd(), 'html', fname[:4])
    output = os.path.join(directory, fname + '.html')
    if os.path.exists(output):
        print('ignore', link)
        return

    print('fetch', link)
    response = requests.get(link, proxies=proxies, headers=headers, timeout=10)
    response.raise_for_status()  # 检查HTTP请求是否成功

    content = response.text

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    safe_write(output,content)

if __name__ == "__main__":
    search_query = "deng xiaoping"
    exact_phrase = ''
    start_page = 1
    end_page = 41
    document_end_date = "2003-06-01" # 固定日期
    
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )

    search_query = "mao zedong"
    exact_phrase = ''
    start_page = 1
    end_page = 8
    document_end_date = "2003-06-01" # 固定日期
    
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )

    search_query = ""
    exact_phrase = 'jiang qing'
    start_page = 1
    end_page = 1
    document_end_date = "2003-06-01" # 固定日期
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )

    search_query = ""
    exact_phrase = 'mao yuanxin'
    start_page = 1
    end_page = 1
    document_end_date = "2003-06-01" # 固定日期
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )

    search_query = ""
    exact_phrase = 'gang of four'
    start_page = 1
    end_page = 39
    document_end_date = "2003-06-01" # 固定日期
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )

    search_query = ""
    exact_phrase = 'mao tse-tung'
    start_page = 1
    end_page = 35
    document_end_date = "2003-06-01" # 固定日期
    
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )

    search_query = ""
    exact_phrase = 'hsiao-ping'
    start_page = 1
    end_page = 50
    document_end_date = "2003-06-01" # 固定日期
    
    print(f"开始抓取维基解密关于 '{search_query}' 的搜索结果 (截止日期: {document_end_date})...")
    fetch_wikileaks_search_results_with_proxy(
        search_query, 
        exact_phrase,
        start_page, 
        end_page, 
        document_date_end=document_end_date,
    )