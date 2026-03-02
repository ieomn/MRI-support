"""
U-Net分割模型
用于MRI病灶区域自动分割
"""
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from loguru import logger
from app.config import settings


class UNet(nn.Module):
    """标准U-Net模型架构"""
    
    def __init__(self, in_channels=1, out_channels=1, init_features=32):
        super(UNet, self).__init__()
        
        features = init_features
        
        # 编码器
        self.encoder1 = self._block(in_channels, features, name="enc1")
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.encoder2 = self._block(features, features * 2, name="enc2")
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.encoder3 = self._block(features * 2, features * 4, name="enc3")
        self.pool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        self.encoder4 = self._block(features * 4, features * 8, name="enc4")
        self.pool4 = nn.MaxPool2d(kernel_size=2, stride=2)
        
        # 瓶颈层
        self.bottleneck = self._block(features * 8, features * 16, name="bottleneck")
        
        # 解码器
        self.upconv4 = nn.ConvTranspose2d(features * 16, features * 8, kernel_size=2, stride=2)
        self.decoder4 = self._block((features * 8) * 2, features * 8, name="dec4")
        
        self.upconv3 = nn.ConvTranspose2d(features * 8, features * 4, kernel_size=2, stride=2)
        self.decoder3 = self._block((features * 4) * 2, features * 4, name="dec3")
        
        self.upconv2 = nn.ConvTranspose2d(features * 4, features * 2, kernel_size=2, stride=2)
        self.decoder2 = self._block((features * 2) * 2, features * 2, name="dec2")
        
        self.upconv1 = nn.ConvTranspose2d(features * 2, features, kernel_size=2, stride=2)
        self.decoder1 = self._block(features * 2, features, name="dec1")
        
        # 输出层
        self.conv = nn.Conv2d(features, out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        # 编码路径
        enc1 = self.encoder1(x)
        enc2 = self.encoder2(self.pool1(enc1))
        enc3 = self.encoder3(self.pool2(enc2))
        enc4 = self.encoder4(self.pool3(enc3))
        
        # 瓶颈
        bottleneck = self.bottleneck(self.pool4(enc4))
        
        # 解码路径
        dec4 = self.upconv4(bottleneck)
        dec4 = torch.cat((dec4, enc4), dim=1)
        dec4 = self.decoder4(dec4)
        
        dec3 = self.upconv3(dec4)
        dec3 = torch.cat((dec3, enc3), dim=1)
        dec3 = self.decoder3(dec3)
        
        dec2 = self.upconv2(dec3)
        dec2 = torch.cat((dec2, enc2), dim=1)
        dec2 = self.decoder2(dec2)
        
        dec1 = self.upconv1(dec2)
        dec1 = torch.cat((dec1, enc1), dim=1)
        dec1 = self.decoder1(dec1)
        
        return self.sigmoid(self.conv(dec1))
    
    @staticmethod
    def _block(in_channels, features, name):
        """U-Net基础卷积块"""
        return nn.Sequential(
            nn.Conv2d(in_channels, features, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(features),
            nn.ReLU(inplace=True),
            nn.Conv2d(features, features, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(features),
            nn.ReLU(inplace=True),
        )


class UNetInferenceService:
    """U-Net推理服务"""
    
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model: Optional[UNet] = None
        self.model_loaded = False
    
    def load_model(self, model_path: Optional[str] = None):
        """加载预训练模型"""
        try:
            if model_path is None:
                model_path = Path(settings.AI_MODEL_PATH) / settings.UNET_MODEL_FILE
            
            if not Path(model_path).exists():
                logger.warning(f"模型文件不存在: {model_path}，将使用随机初始化模型（仅用于测试）")
                self.model = UNet(in_channels=1, out_channels=1).to(self.device)
                self.model.eval()
                self.model_loaded = True
                return
            
            # 加载模型权重
            self.model = UNet(in_channels=1, out_channels=1).to(self.device)
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self.model_loaded = True
            
            logger.info(f"U-Net模型加载成功: {model_path}")
            
        except Exception as e:
            logger.error(f"U-Net模型加载失败: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """
        预处理输入影像
        :param image: numpy数组 (H, W) 或 (H, W, 1)
        :return: torch张量 (1, 1, H, W)
        """
        # 确保是2D
        if len(image.shape) == 3:
            image = image[:, :, 0]
        
        # 归一化到[0, 1]
        image = image.astype(np.float32)
        image = (image - image.min()) / (image.max() - image.min() + 1e-8)
        
        # 转换为torch张量并添加批次和通道维度
        tensor = torch.from_numpy(image).unsqueeze(0).unsqueeze(0)
        return tensor.to(self.device)
    
    def postprocess_mask(self, output: torch.Tensor, threshold: float = 0.5) -> np.ndarray:
        """
        后处理输出掩码
        :param output: 模型输出 (1, 1, H, W)
        :param threshold: 二值化阈值
        :return: numpy数组 (H, W)
        """
        # 转换为numpy并去除批次和通道维度
        mask = output.squeeze().cpu().numpy()
        
        # 二值化
        mask = (mask > threshold).astype(np.uint8)
        
        return mask
    
    @torch.no_grad()
    def predict(
        self,
        image: np.ndarray,
        threshold: float = 0.5
    ) -> Tuple[np.ndarray, float]:
        """
        执行分割预测
        :param image: 输入影像
        :param threshold: 分割阈值
        :return: (分割掩码, 置信度)
        """
        if not self.model_loaded:
            self.load_model()
        
        try:
            # 预处理
            input_tensor = self.preprocess_image(image)
            
            # 推理
            output = self.model(input_tensor)
            
            # 计算平均置信度
            confidence = output.mean().item()
            
            # 后处理
            mask = self.postprocess_mask(output, threshold)
            
            return mask, confidence
            
        except Exception as e:
            logger.error(f"U-Net推理失败: {e}")
            raise
    
    def batch_predict(
        self,
        images: list[np.ndarray],
        threshold: float = 0.5
    ) -> list[Tuple[np.ndarray, float]]:
        """批量预测（用于多切片MRI）"""
        results = []
        for img in images:
            mask, confidence = self.predict(img, threshold)
            results.append((mask, confidence))
        return results
    
    def calculate_tumor_volume(
        self,
        masks: list[np.ndarray],
        pixel_spacing: Tuple[float, float],
        slice_thickness: float
    ) -> float:
        """
        计算肿瘤体积
        :param masks: 分割掩码列表
        :param pixel_spacing: 像素间距 (mm)
        :param slice_thickness: 层厚 (mm)
        :return: 体积 (cm³)
        """
        # 计算每个像素的体积 (mm³)
        voxel_volume = pixel_spacing[0] * pixel_spacing[1] * slice_thickness
        
        # 统计所有掩码中的阳性像素数
        total_voxels = sum(mask.sum() for mask in masks)
        
        # 转换为cm³
        volume_mm3 = total_voxels * voxel_volume
        volume_cm3 = volume_mm3 / 1000.0
        
        return volume_cm3


# 全局推理服务实例
unet_service = UNetInferenceService()

