import torch
from torchvision import models, transforms
from PIL import Image
import numpy as np
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self, model_path=None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_or_create_model(model_path)
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        logger.info(f"ImageAnalyzer initialized using device: {self.device}")
        
    def _load_or_create_model(self, model_path):
        try:
            if model_path:
                model_full_path = os.path.join(settings.BASE_DIR, model_path)
                if os.path.exists(model_full_path):
                    logger.info(f"Loading model from {model_full_path}")
                    if torch.cuda.is_available():
                        return torch.load(model_full_path)
                    else:
                        return torch.load(model_full_path, map_location=self.device)
                else:
                    logger.warning(f"Model path {model_full_path} not found, creating new model")
            return self._create_model()
        except Exception as e:
            logger.error(f"Error loading model: {e}, creating new model instead")
            return self._create_model()
    
    def _create_model(self):
        logger.info("Creating new model")
        # Use ResNet50 as base model
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        
        # Modify the final layer for binary classification
        num_features = model.fc.in_features
        model.fc = torch.nn.Sequential(
            torch.nn.Linear(num_features, 1024),
            torch.nn.ReLU(),
            torch.nn.Dropout(0.2),
            torch.nn.Linear(1024, 1),
            torch.nn.Sigmoid()
        )
        
        # Move model to appropriate device (GPU/CPU)
        model = model.to(self.device)
        
        # Set model to evaluation mode
        model.eval()
        
        return model
    
    def preprocess_image(self, image_path):
        """Preprocess image for model input"""
        try:
            img = Image.open(image_path).convert('RGB')
            img_tensor = self.transform(img)
            img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
            return img_tensor.to(self.device)
        except Exception as e:
            logger.error(f"Error preprocessing image: {e}")
            raise
    
    def analyze_image(self, image_path):
        """Analyze an image and return prediction"""
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image path does not exist: {image_path}")
                return None

            with torch.no_grad():
                img_tensor = self.preprocess_image(image_path)
                prediction = self.model(img_tensor)
                prob = prediction.item()
                
                return {
                    'is_real': bool(prob > 0.5),
                    'confidence': float(prob if prob > 0.5 else 1 - prob)
                }
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

# Initialize the model with pretrained weights
MODEL_PATH = os.path.join('detector', 'models', 'realface_model.pth')
analyzer = ImageAnalyzer(model_path=MODEL_PATH)