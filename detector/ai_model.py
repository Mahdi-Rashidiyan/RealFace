import torch
from torchvision import models, transforms
from PIL import Image
import numpy as np
import os
import gc
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ImageAnalyzer:
    def __init__(self, model_path=None):
        # Force CPU usage for Render deployment
        self.device = torch.device('cpu')
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.model = self._load_or_create_model(model_path)
        logger.info(f"ImageAnalyzer initialized using device: {self.device}")
        
    def _load_or_create_model(self, model_path):
        try:
            if model_path and os.path.exists(os.path.join(settings.BASE_DIR, model_path)):
                model_full_path = os.path.join(settings.BASE_DIR, model_path)
                logger.info(f"Loading model from {model_full_path}")
                
                # Create model first - with minimal memory usage
                model = self._create_model(initialize_weights=False)
                
                # Load state dict
                try:
                    # Load state_dict with the new weight_only=True (default in PyTorch 2.6+)
                    state_dict = torch.load(model_full_path, map_location=self.device)
                    model.load_state_dict(state_dict)
                    logger.info("Successfully loaded model weights")
                    
                    # Force garbage collection to free memory
                    gc.collect()
                    torch.cuda.empty_cache()  # Won't hurt even on CPU
                    
                    return model
                    
                except Exception as e:
                    logger.error(f"Error loading model weights: {e}")
                    logger.warning("IMPORTANT: Using an untrained model. Analysis results will be random.")
                    return self._create_model(memory_efficient=True)
            else:
                if model_path:
                    logger.warning(f"Model path {os.path.join(settings.BASE_DIR, model_path)} not found, creating new model")
                logger.warning("IMPORTANT: Using an untrained model. Analysis results will be random.")
                logger.warning("Run the train_model.py script to create a properly trained model file.")
                return self._create_model(memory_efficient=True)
        except Exception as e:
            logger.error(f"Error loading model: {e}, creating new model instead")
            logger.warning("IMPORTANT: Using an untrained model. Analysis results will be random.")
            return self._create_model(memory_efficient=True)
    
    def _create_model(self, initialize_weights=True, memory_efficient=False):
        logger.info("Creating new model")
        
        # Use lightweight model for Render's free tier if memory_efficient is True
        if memory_efficient:
            model = models.mobilenet_v2(weights=None)
            # Modify the classifier for binary classification
            model.classifier = torch.nn.Sequential(
                torch.nn.Dropout(0.2),
                torch.nn.Linear(model.last_channel, 1),
                torch.nn.Sigmoid()
            )
        else:
            # Use ResNet50 as base model with pretrained weights if requested
            if initialize_weights:
                model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            else:
                model = models.resnet50(weights=None)
            
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
        
        # Force garbage collection
        gc.collect()
        torch.cuda.empty_cache()  # Won't hurt even on CPU
        
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
                
                # Clear memory
                del img_tensor
                gc.collect()
                
                return {
                    'is_real': bool(prob > 0.5),
                    'confidence': float(prob if prob > 0.5 else 1 - prob)
                }
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            return None

# Create the models directory if it doesn't exist
models_dir = os.path.join(settings.BASE_DIR, 'detector', 'models')
if not os.path.exists(models_dir):
    os.makedirs(models_dir)
    logger.info(f"Created missing models directory: {models_dir}")

# Initialize the model with pretrained weights
MODEL_PATH = os.path.join('detector', 'models', 'realface_model.pth')
analyzer = ImageAnalyzer(model_path=MODEL_PATH)