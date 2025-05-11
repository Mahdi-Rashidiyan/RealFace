import torch
import torch.nn as nn
from torchvision import models
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(parent_dir))

# Now we can import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realface.settings')
import django
django.setup()

from django.conf import settings

def create_dummy_model():
    print("Creating a dummy model for testing...")
    
    # Initialize model
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
    num_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(num_features, 1024),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(1024, 1),
        nn.Sigmoid()
    )
    
    # Set model to evaluation mode
    model.eval()
    
    # Save model's state_dict instead of the full model
    model_path = os.path.join(settings.BASE_DIR, 'detector', 'models', 'realface_model.pth')
    torch.save(model.state_dict(), model_path)
    print(f"Dummy model saved to: {model_path}")
    print("This is an UNTRAINED model and will produce random results.")
    print("For actual use, train a proper model using train_model.py")

if __name__ == '__main__':
    create_dummy_model() 