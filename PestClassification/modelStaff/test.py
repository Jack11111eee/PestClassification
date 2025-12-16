# ==============================================================================
#  test.py - 使用测试集评估最终模型的性能
# ==============================================================================
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import torchvision.transforms as T
from torchvision.models import resnet50
from tqdm import tqdm
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import pandas as pd
import numpy as np

# --- 1. 配置参数 ---
# 模型权重路径 (使用你训练好的那个!)
MODEL_PATH = '/home/jovyan/notebook/Agri/ResNet50_20251103_080707.pth' 
# 数据集根目录
DATA_DIR = '/home/jovyan/notebook/Agri/PlantDiseases_Final_Split'
# 测试集路径
TEST_DIR = os.path.join(DATA_DIR, 'test')
# 类别数量
NUM_CLASSES = 42
# 其他配置
BATCH_SIZE = 32
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# 报告保存路径
REPORT_SAVE_PATH = '/home/jovyan/notebook/Agri/test_report.txt'
CONFUSION_MATRIX_SAVE_PATH = '/home/jovyan/notebook/Agri/confusion_matrix.png'

print("--- Configuration ---")
print(f"Model Path: {MODEL_PATH}")
print(f"Test Data Path: {TEST_DIR}")
print(f"Device: {DEVICE}\n")

# --- 2. 数据加载与预处理 ---
# 预处理必须和验证集完全一样
test_transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

test_dataset = ImageFolder(root=TEST_DIR, transform=test_transform)
test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

class_names = test_dataset.classes
print(f"Found {len(test_dataset)} images in test set, belonging to {len(class_names)} classes.\n")

# --- 3. 定义模型并加载权重 ---
model = resnet50(weights=None)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, NUM_CLASSES)

model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.to(DEVICE)
model.eval() # !!! 必须设置为评估模式 !!!
print("Model loaded and set to evaluation mode.\n")

# --- 4. 执行测试 ---
all_preds = []
all_labels = []

print("--- Starting Evaluation on Test Set ---")
# 使用tqdm显示进度条
test_pbar = tqdm(test_loader, desc="Testing")

with torch.no_grad():
    for inputs, labels in test_pbar:
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
        
        outputs = model(inputs)
        _, preds = torch.max(outputs, 1)
        
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

print("\n--- Evaluation Complete ---\n")

# --- 5. 生成并打印/保存报告 ---

# 计算总体准确率
accuracy = accuracy_score(all_labels, all_preds)
print(f"Overall Test Accuracy: {accuracy:.4f} ({accuracy:.2%})\n")

# 生成详细分类报告
report = classification_report(all_labels, all_preds, target_names=class_names, digits=4)
print("--- Classification Report ---")
print(report)

# 将报告保存到文件
with open(REPORT_SAVE_PATH, 'w') as f:
    f.write("Overall Test Accuracy\n")
    f.write(f"{accuracy:.4f} ({accuracy:.2%})\n\n")
    f.write("--- Classification Report ---\n")
    f.write(report)
print(f"Test report saved to: {REPORT_SAVE_PATH}\n")


# --- 6. 生成并保存混淆矩阵 ---
print("--- Generating Confusion Matrix ---")
cm = confusion_matrix(all_labels, all_preds)
cm_df = pd.DataFrame(cm, index=class_names, columns=class_names)

plt.style.use('default') # 使用默认样式以获得更好的清晰度
plt.figure(figsize=(20, 17))
sns.heatmap(cm_df, annot=True, fmt='d', cmap='Blues')
plt.title(f'Confusion Matrix | Test Accuracy: {accuracy:.3f}', fontsize=16)
plt.ylabel('True Label', fontsize=14)
plt.xlabel('Predicted Label', fontsize=14)
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(CONFUSION_MATRIX_SAVE_PATH)

print(f"Confusion matrix saved to: {CONFUSION_MATRIX_SAVE_PATH}")
print("\n🎉 All tasks completed!")
