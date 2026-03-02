"""
初始化演示数据
"""
from database_standalone import SessionLocal
from models_standalone import Patient
from datetime import date, datetime


def init_demo_data():
    """创建演示数据"""
    db = SessionLocal()
    
    try:
        # 检查是否已有数据
        if db.query(Patient).count() > 0:
            print("数据库已有数据，跳过初始化")
            return
        
        # 创建演示患者
        demo_patients = [
            Patient(
                patient_no="EC202511050001",
                name="张女士",
                gender="female",
                birth_date=date(1955, 3, 15),
                phone="138****1234",
                address="青海省西宁市城东区",
                admission_date=date(2025, 10, 1),
                hospital="青海省第五人民医院",
                diagnosis="子宫内膜癌",
                stage="II",
            ),
            Patient(
                patient_no="EC202511050002",
                name="李女士",
                gender="female",
                birth_date=date(1960, 7, 22),
                phone="139****5678",
                address="青海省西宁市城西区",
                admission_date=date(2025, 10, 15),
                hospital="青海省第五人民医院",
                diagnosis="子宫内膜癌",
                stage="I",
            ),
            Patient(
                patient_no="EC202511050003",
                name="王女士",
                gender="female",
                birth_date=date(1958, 12, 8),
                phone="136****9012",
                address="青海省海东市",
                admission_date=date(2025, 10, 20),
                hospital="青海省第五人民医院",
                diagnosis="子宫内膜癌",
                stage="III",
            ),
        ]
        
        for patient in demo_patients:
            db.add(patient)
        
        db.commit()
        print(f"✓ 已创建 {len(demo_patients)} 个演示患者")
        
    except Exception as e:
        print(f"初始化演示数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("初始化演示数据...")
    init_demo_data()
    print("完成！")

