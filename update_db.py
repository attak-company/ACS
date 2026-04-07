from app import create_app
from shared.database import db
from sqlalchemy import text

def init_db():
    app = create_app()
    with app.app_context():
        # 1. 確保所有資料表都已建立 (如果不存在)
        db.create_all()
        
        # 2. 手動為 services 資料表新增 color 欄位 (如果不存在)
        try:
            db.session.execute(text("ALTER TABLE services ADD COLUMN color VARCHAR(20) DEFAULT '#007bff'"))
            db.session.commit()
            print("✅ Successfully added 'color' column to 'services' table")
        except Exception as e:
            # 如果欄位已存在，這裡會報錯，我們可以忽略它
            db.session.rollback()
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️ Column 'color' already exists in 'services' table")
            else:
                print(f"❌ Error adding column: {e}")
                
        print("✅ Database maintenance completed")

if __name__ == "__main__":
    init_db()
