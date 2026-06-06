#!/usr/bin/env python3
"""URL XOR 加密工具"""
import sys

def xor_encrypt(text, key):
    """XOR 加密函数"""
    result = []
    for i, char in enumerate(text):
        result.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return ''.join(result)

if __name__ == "__main__":
    url = input("请输入要加密的 URL: ").strip()
    key = input("请输入加密密钥: ").strip()

    encrypted = xor_encrypt(url, key)
    print(f"\n加密后的字符串: {encrypted}")
    print(f"\n将以下内容填入 utils.py:")
    print(f'ENCRYPTED_URL = "{encrypted}"')
    print(f'XOR_KEY = "{key}"')
