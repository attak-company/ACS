
import sys
import os
sys.path.insert(0, '.')

from app import create_app
from shared.database import db
from shared.models import Merchant

from dotenv import load_dotenv

def update_credentials():
    load_dotenv()
    app = create_app()
    with app.app_context():
        m = Merchant.query.first()
        if m:
            print(f"正在更新商家 '{m.name}' 的金鑰...")
            m.line_channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
            m.line_channel_secret = os.getenv('LINE_CHANNEL_SECRET')
            m.google_gemini_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
            db.session.commit()
            print("✅ 金鑰已成功從 .env 同步至資料庫")
        else:
            print("❌ 找不到商家資料，無法更新")

if __name__ == '__main__':
    update_credentials()
