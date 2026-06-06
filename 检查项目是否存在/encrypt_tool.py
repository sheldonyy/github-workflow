#!/usr/bin/env python3
"""URL 加密工具 - 生成可复制的加密字符串"""
import base64
import sys

def encrypt_url(url, key):
    """Base64 编码后再 XOR 加密"""
    b64_encoded = base64.b64encode(url.encode('utf-8')).decode('utf-8')
    result = []
    for i, char in enumerate(b64_encoded):
        result.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return ''.join(result)

if __name__ == "__main__":
    url = "https://www.acgndog.com/"
    key = "acgn"

    encrypted = encrypt_url(url, key)

    # 输出可以直接粘贴到 Python 代码中的格式
    print(f"URL: {url}")
    print(f"Key: {key}")
    print(f"加密后: {repr(encrypted)}")
    print()
    print("=" * 50)
    print("复制以下内容到 utils.py:")
    print("=" * 50)
    print(f'ENCRYPTED_URL = "{encrypted}"')
    print(f'XOR_KEY = "{key}"')
