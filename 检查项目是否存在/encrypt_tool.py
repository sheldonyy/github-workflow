#!/usr/bin/env python3
"""URL 加密工具 - 生成 Base64 编码字符串"""
import base64

def encrypt_url(url):
    """Base64 编码"""
    return base64.b64encode(url.encode('utf-8')).decode('utf-8')

if __name__ == "__main__":
    url = "https://www.acgndog.com/"

    encrypted = encrypt_url(url)

    print(f"URL: {url}")
    print(f"加密后: {encrypted}")
    print()
    print("复制以下内容到 utils.py:")
    print(f'ENCODED_URL = "{encrypted}"')
