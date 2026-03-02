"""
线性回归预后预测模型
用于评估患者的复发风险和生存期预测
"""
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Optional
from sklearn.linear_model import LinearRegression
from loguru import logger
from app.config import settings


class PrognosisRegressionService:
    """预后预测回归服务"""
    
    def __init__(self):
        self.model: Optional[LinearRegression] = None
        self.feature_names: list[str] = [
            # 临床特征
            "age",                      # 年龄
            "bmi",                      # BMI
            
            # 病理特征
            "stage_numeric",            # 分期(数值化: I=1, II=2, III=3, IV=4)
            "grade_numeric",            # 分级(数值化: 1-3)
            "tumor_size",               # 肿瘤大小(cm)
            "lymph_node_positive",      # 淋巴结阳性数量
            
            # 影像组学特征
            "tumor_volume",             # 肿瘤体积(cm³)
            "shape_sphericity",         # 形状球形度
            "intensity_mean",           # 平均强度
            "intensity_std",            # 强度标准差
            "texture_contrast",         # 纹理对比度
            "texture_entropy",          # 纹理熵
        ]
        self.model_loaded = False
    
    def load_model(self, model_path: Optional[str] = None):
        """加载预训练回归模型"""
        try:
            if model_path is None:
                model_path = Path(settings.AI_MODEL_PATH) / settings.REGRESSION_MODEL_FILE
            
            if not Path(model_path).exists():
                logger.warning(f"模型文件不存在: {model_path}，将使用默认模型（仅用于测试）")
                # 创建一个简单的模型用于演示
                self.model = LinearRegression()
                # 使用随机权重初始化
                self.model.coef_ = np.random.randn(len(self.feature_names))
                self.model.intercept_ = 0.5
                self.model_loaded = True
                return
            
            # 加载模型
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.feature_names = model_data.get('feature_names', self.feature_names)
            
            self.model_loaded = True
            logger.info(f"回归模型加载成功: {model_path}")
            
        except Exception as e:
            logger.error(f"回归模型加载失败: {e}")
            raise
    
    def extract_clinical_features(self, patient_data: Dict) -> np.ndarray:
        """
        从患者数据中提取特征向量
        :param patient_data: 患者数据字典
        :return: 特征向量
        """
        features = []
        
        # 临床特征
        features.append(patient_data.get('age', 65))
        features.append(patient_data.get('bmi', 24.0))
        
        # 病理特征
        stage_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
        stage = patient_data.get('stage', 'II')
        features.append(stage_map.get(stage, 2))
        
        grade = patient_data.get('grade', 2)
        features.append(int(grade) if isinstance(grade, (int, str)) else 2)
        
        features.append(patient_data.get('tumor_size', 3.0))
        features.append(patient_data.get('lymph_node_positive', 0))
        
        # 影像组学特征
        radiomics = patient_data.get('radiomics_features', {})
        features.append(radiomics.get('tumor_volume', 5.0))
        features.append(radiomics.get('shape_sphericity', 0.7))
        features.append(radiomics.get('intensity_mean', 100.0))
        features.append(radiomics.get('intensity_std', 20.0))
        features.append(radiomics.get('texture_contrast', 50.0))
        features.append(radiomics.get('texture_entropy', 3.5))
        
        return np.array(features).reshape(1, -1)
    
    def predict_prognosis(self, patient_data: Dict) -> Dict:
        """
        预测患者预后
        :param patient_data: 患者数据
        :return: 预测结果字典
        """
        if not self.model_loaded:
            self.load_model()
        
        try:
            # 提取特征
            features = self.extract_clinical_features(patient_data)
            
            # 预测
            risk_score = self.model.predict(features)[0]
            
            # 限制评分范围到[0, 1]
            risk_score = np.clip(risk_score, 0, 1)
            
            # 根据评分划分风险等级
            if risk_score < 0.3:
                risk_level = "low"
                risk_level_zh = "低风险"
            elif risk_score < 0.7:
                risk_level = "medium"
                risk_level_zh = "中风险"
            else:
                risk_level = "high"
                risk_level_zh = "高风险"
            
            # 计算复发概率（简化模型）
            recurrence_prob_2yr = risk_score * 0.4  # 2年复发概率
            recurrence_prob_5yr = risk_score * 0.6  # 5年复发概率
            
            # 生存期预测（简化）
            survival_1yr = 1.0 - (risk_score * 0.1)
            survival_3yr = 1.0 - (risk_score * 0.3)
            survival_5yr = 1.0 - (risk_score * 0.5)
            
            result = {
                "prognosis_score": float(risk_score),
                "risk_level": risk_level,
                "risk_level_zh": risk_level_zh,
                "recurrence_probability": {
                    "2_year": float(recurrence_prob_2yr),
                    "5_year": float(recurrence_prob_5yr),
                },
                "survival_prediction": {
                    "1_year": float(survival_1yr),
                    "3_year": float(survival_3yr),
                    "5_year": float(survival_5yr),
                },
                "feature_importance": self._get_feature_importance(),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"预后预测失败: {e}")
            raise
    
    def _get_feature_importance(self) -> Dict[str, float]:
        """获取特征重要性（基于回归系数）"""
        if self.model is None:
            return {}
        
        # 获取系数的绝对值作为重要性
        importance = np.abs(self.model.coef_)
        
        # 归一化
        importance = importance / importance.sum()
        
        # 构建字典
        importance_dict = {
            name: float(imp)
            for name, imp in zip(self.feature_names, importance)
        }
        
        # 排序（降序）
        importance_dict = dict(
            sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
        )
        
        return importance_dict


# 全局服务实例
regression_service = PrognosisRegressionService()

