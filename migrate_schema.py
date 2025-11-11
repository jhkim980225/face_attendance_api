"""
데이터베이스 스키마 마이그레이션: user_embeddings 테이블 제거
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def migrate():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # users 테이블에 embedding_path 컬럼 추가 (이미 있으면 무시)
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN embedding_path VARCHAR(255) NULL"))
            print("✅ embedding_path 컬럼 추가 완료")
        except Exception as e:
            print(f"⚠️  embedding_path 컬럼: {e}")
        
        # user_embeddings 테이블 삭제
        try:
            conn.execute(text("DROP TABLE IF EXISTS user_embeddings"))
            print("✅ user_embeddings 테이블 삭제 완료")
        except Exception as e:
            print(f"❌ 테이블 삭제 실패: {e}")
        
        conn.commit()
    
    print("\n🎉 마이그레이션 완료!")

if __name__ == "__main__":
    migrate()
