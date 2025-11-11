"""
사용자 테이블 초기화 (재등록을 위해)
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def reset():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 모든 사용자 삭제
        conn.execute(text("DELETE FROM users"))
        conn.commit()
        print("✅ 모든 사용자 삭제 완료!")
        print("📝 이제 다시 등록해주세요.")

if __name__ == "__main__":
    reset()
