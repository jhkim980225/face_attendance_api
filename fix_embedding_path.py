"""
기존 사용자의 profile_image를 임베딩 경로로 수정
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_paths():
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 모든 사용자 조회
        result = conn.execute(text("SELECT employee_id, profile_image FROM users"))
        users = result.fetchall()
        
        for user in users:
            employee_id = user[0]
            # 임베딩 경로는 app\static\encodings\{employee_id}.npy
            new_path = f"app\\static\\encodings\\{employee_id}.npy"
            
            conn.execute(
                text("UPDATE users SET profile_image = :path WHERE employee_id = :emp_id"),
                {"path": new_path, "emp_id": employee_id}
            )
            print(f"✅ {employee_id}: {new_path}")
        
        conn.commit()
    
    print("\n🎉 경로 수정 완료!")

if __name__ == "__main__":
    fix_paths()
