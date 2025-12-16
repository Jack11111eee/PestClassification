import torch
from torchvision import transforms, datasets
from torch.utils.data import DataLoader, ConcatDataset
from model import your_model_class # 假设你的模型定义在model.py中

# --- 参数配置 ---
ORIGINAL_DATA_PATH = '/home/hzcu/PlantDiseases_Final_Split' # 你最初的训练集路径
FEEDBACK_DATA_PATH = '/home/hzcu/outcomes/feedback_data'
MODEL_LOAD_PATH = '/home/jovyan/notebook/Agri/ResNet50_v1.pth' # 当前线上的模型
MODEL_SAVE_PATH = '/home/jovyan/notebook/Agri/ResNet50_v2.pth' # 新模型保存路径
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# --- 数据加载 ---
# 定义和训练时一样的数据预处理
data_transform = transforms.Compose([
    transforms.RandomResizedCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 加载原始数据集和新的反馈数据集
original_dataset = datasets.ImageFolder(ORIGINAL_DATA_PATH, transform=data_transform)
feedback_dataset = datasets.ImageFolder(FEEDBACK_DATA_PATH, transform=data_transform)

# 合并两个数据集
combined_dataset = ConcatDataset([original_dataset, feedback_dataset])
train_loader = DataLoader(combined_dataset, batch_size=32, shuffle=True)

print(f"原始数据量: {len(original_dataset)}, 反馈数据量: {len(feedback_dataset)}, 总数据量: {len(combined_dataset)}")

# --- 模型加载和微调 (Fine-tuning) ---
# 加载你现有的模型
model = your_model_class(num_classes=42) # 确保这里的参数正确
model.load_state_dict(torch.load(MODEL_LOAD_PATH, map_location=DEVICE))
model.to(DEVICE)

# 定义损失函数和优化器
criterion = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.0001) # 使用一个较小的学习率进行微调

# --- 开始训练 ---
num_epochs = 5 # 在新数据上训练少量轮次即可
model.train()
for epoch in range(num_epochs):
    running_loss = 0.0
    for images, labels in train_loader:
        images, labels = images.to(DEVICE), labels.to(DEVICE)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item() * images.size(0)
    
    epoch_loss = running_loss / len(train_loader.dataset)
    print(f"Epoch {epoch+1}/{num_epochs}, Loss: {epoch_loss:.4f}")

# --- 保存新模型 ---
torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"新的模型已训练完成并保存至: {MODEL_SAVE_PATH}")
