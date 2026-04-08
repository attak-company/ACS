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

        # 3. 手動為 merchants 資料表新增 Instagram 欄位 (如果不存在)
        for sql, column_name in [
            ("ALTER TABLE merchants ADD COLUMN instagram_username VARCHAR(100)", "instagram_username"),
            ("ALTER TABLE merchants ADD COLUMN instagram_url VARCHAR(255)", "instagram_url"),
            ("ALTER TABLE merchants ADD COLUMN instagram_page_access_token VARCHAR(255)", "instagram_page_access_token"),
            ("ALTER TABLE merchants ADD COLUMN instagram_verify_token VARCHAR(120)", "instagram_verify_token"),
        ]:
            try:
                db.session.execute(text(sql))
                db.session.commit()
                print(f"✅ Successfully added '{column_name}' column to 'merchants' table")
            except Exception as e:
                db.session.rollback()
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print(f"ℹ️ Column '{column_name}' already exists in 'merchants' table")
                else:
                    print(f"❌ Error adding '{column_name}' column: {e}")
                
        print("✅ Database maintenance completed")

if __name__ == "__main__":
    init_db()
