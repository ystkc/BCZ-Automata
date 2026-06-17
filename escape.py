# escape.py
'''【调试工具】将剪切板中的令牌转义'''
import pyperclip

text = pyperclip.paste()
text = text.replace('/', '%2F').replace('+', '%2B').replace('=', '%3D')
pyperclip.copy(text)