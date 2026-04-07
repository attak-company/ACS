#!/usr/bin/env python3
"""
測試模板載入問題
"""

import sys
sys.path.insert(0, '.')

from flask import Flask, render_template

def test_template():
    """測試模板載入"""
    print("🔍 測試模板載入...")
    
    app = Flask(__name__, template_folder='web_modules/templates')
    
    with app.test_request_context('/'):
        try:
            # 測試 landing.html
            result = render_template('landing.html')
            print("✅ landing.html 載入成功")
            print(f"   內容長度: {len(result)} 字符")
            
            # 測試 index.html
            result2 = render_template('index.html')
            print("✅ index.html 載入成功")
            print(f"   內容長度: {len(result2)} 字符")
            
        except Exception as e:
            print(f"❌ 模板載入失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_template()
