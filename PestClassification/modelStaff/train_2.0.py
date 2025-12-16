# ==============================================================================
#  train.py - V2 (带日志和绘图功能)
# ==============================================================================
import os
import time
import datetime
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder
import torchvision.transforms as T
from torchvision.models import resnet50, ResNet50_Weights
import matplotlib.pyplot as plt
from tqdm import tqdm

# --- 1. 配置参数 (你可以在这里调整) ---
# 数据集路径
DATA_DIR = '/home/jovyan/notebook/Agri/PlantDiseases_Final_Split'
# 模型名称，用于保存文件
MODEL_NAME = 'ResNet50'
# 训练超参数
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LEARNING_RATE = 0.001
BATCH_SIZE = 32
EPOCHS = 10  

# --- 新增：文件路径配置 ---
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
# 模型保存路径
MODEL_SAVE_PATH = f'/home/jovyan/notebook/Agri/{MODEL_NAME}_{TIMESTAMP}.pth'
# 日志文件路径
LOG_FILE_PATH = f'/home/jovyan/notebook/Agri/training_log_{TIMESTAMP}.log'
# 结果图路径
PLOT_FILE_PATH = f'/home/jovyan/notebook/Agri/accuracy_loss_curve_{MODEL_NAME}_{TIMESTAMP}.png'


# --- 新增：设置日志记录 ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(LOG_FILE_PATH),
                        logging.StreamHandler() # 同时输出到控制台
                    ])

# --- 打印和记录配置信息 ---
logging.info("--- Configuration ---")
logging.info(f"Model: {MODEL_NAME}")
logging.info(f"Device: {DEVICE}")
logging.info(f"Data Directory: {DATA_DIR}")
logging.info(f"Model will be saved to: {MODEL_SAVE_PATH}")
logging.info(f"Learning Rate: {LEARNING_RATE}, Batch Size: {BATCH_SIZE}, Epochs: {EPOCHS}\n")

# --- 2. 数据加载与预处理 ---
logging.info("--- Step 2: Preparing DataLoaders ---")
train_transform = T.Compose([
    T.RandomResizedCrop(224), T.RandomHorizontalFlip(),
    T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    T.ToTensor(), T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
val_test_transform = T.Compose([
    T.Resize(256), T.CenterCrop(224), T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

train_dataset = ImageFolder(root=os.path.join(DATA_DIR, 'train'), transform=train_transform)
val_dataset = ImageFolder(root=os.path.join(DATA_DIR, 'val'), transform=val_test_transform)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=4, pin_memory=True)
val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

num_classes = len(train_dataset.classes)
logging.info(f"Data loading complete. Found {num_classes} classes.")
logging.info(f"Training samples: {len(train_dataset)}, Validation samples: {len(val_dataset)}\n")

# --- 3. 模型定义 ---
logging.info("--- Step 3: Building Model ---")
model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
num_ftrs = model.fc.in_features
model.fc = nn.Linear(num_ftrs, num_classes)
model = model.to(DEVICE)
logging.info("Model built and moved to device.\n")

# --- 4. 定义损失函数和优化器 ---
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# --- 5. 训练与验证循环 ---
logging.info("--- Step 5: Starting Training ---")
best_val_accuracy = 0.0

# 新增：用于绘图的数据记录列表
history = {
    'train_loss': [], 'train_acc': [],
    'val_loss': [], 'val_acc': []
}

for epoch in range(EPOCHS):
    start_time = time.time()
    
    # 训练
    model.train()
    running_loss, train_corrects = 0.0, 0
    train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Train]")
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * inputs.size(0)
        _, preds = torch.max(outputs, 1)
        train_corrects += torch.sum(preds == labels.data)

        train_pbar.set_postfix(loss=loss.item(), acc=train_corrects.double().item() / ((train_pbar.n + 1) * BATCH_SIZE))
    
    train_loss = running_loss / len(train_dataset)
    train_acc = train_corrects.double() / len(train_dataset)
    history['train_loss'].append(train_loss)
    history['train_acc'].append(train_acc.item())

    # 验证
    model.eval()
    val_loss, val_corrects = 0.0, 0
    val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Val]")
    with torch.no_grad():
        for inputs, labels in val_loader:
            inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            val_loss += loss.item() * inputs.size(0)
            _, preds = torch.max(outputs, 1)
            val_corrects += torch.sum(preds == labels.data)

            val_pbar.set_postfix(loss=loss.item(), acc=val_corrects.double().item() / ((val_pbar.n + 1) * BATCH_SIZE))
            
    val_loss = val_loss / len(val_dataset)
    val_acc = val_corrects.double() / len(val_dataset)
    history['val_loss'].append(val_loss)
    history['val_acc'].append(val_acc.item())

    epoch_time = time.time() - start_time
    
    log_message = (f"Epoch {epoch+1}/{EPOCHS} | "
                   f"Time: {epoch_time:.0f}s | "
                   f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f} | "
                   f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}")
    logging.info(log_message)
          
    if val_acc > best_val_accuracy:
        best_val_accuracy = val_acc
        torch.save(model.state_dict(), MODEL_SAVE_PATH)
        logging.info(f"    -> Validation accuracy improved. Model saved to {MODEL_SAVE_PATH}")

logging.info("\n--- Training Complete ---")
logging.info(f"🎉 Best Validation Accuracy: {best_val_accuracy:.4f}")
logging.info(f"Final model state saved at: {MODEL_SAVE_PATH}")


# --- 6. 新增功能：绘制并保存结果图 ---
logging.info("\n--- Step 6: Plotting and saving a summary graph ---")
plt.style.use('ggplot')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12))

# 绘制精度曲线
ax1.plot(history['train_acc'], label='Train Accuracy')
ax1.plot(history['val_acc'], label='Validation Accuracy')
ax1.set_ylabel('Accuracy')
ax1.set_title(f'Accuracy Curve - {MODEL_NAME} ({TIMESTAMP})')
ax1.legend()

# 绘制损失曲线
ax2.plot(history['train_loss'], label='Train Loss')
ax2.plot(history['val_loss'], label='Validation Loss')
ax2.set_ylabel('Loss')
ax2.set_xlabel('Epochs')
ax2.set_title(f'Loss Curve - {MODEL_NAME} ({TIMESTAMP})')
ax2.legend()

plt.tight_layout()
plt.savefig(PLOT_FILE_PATH)
logging.info(f"Accuracy/Loss graph saved to {PLOT_FILE_PATH}")
