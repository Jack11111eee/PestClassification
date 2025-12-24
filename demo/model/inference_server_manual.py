import os
import io
import uuid
import threading
import torch
import shutil
import torchvision.transforms as T
from torchvision import datasets
from torch.utils.data import DataLoader, ConcatDataset
from torchvision.models import resnet50
from flask import Flask, request, jsonify
from PIL import Image
import time
import sys

# ================= 1. 全局配置 =================
BASE_DIR = '/home/hzcu/repo/modelStaff'
# 权重路径
MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_v1.pth')      
BEST_MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_best.pth') 
# 数据路径
FEEDBACK_DIR = os.path.join(BASE_DIR, 'feedback_data')        
ARCHIVE_DIR = os.path.join(BASE_DIR, 'archived_feedback')     
ORIGINAL_DATASET_DIR = '/home/hzcu/PlantDiseases_Final_Split' 

RETRAIN_THRESHOLD = 100
PORT = 5001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 类别定义 (必须与训练时严格一致)
raw_classes = [
    'Apple_Black_Rot', 'Apple_Cedar_Apple_Rust', 'Apple_healthy', 'Apple_Scab', 
    'Blueberry_healthy', 'Cherry_healthy', 'Cherry_Powdery_Mildew', 
    'Corn_Common_Rust', 'Corn_Gray_Leaf_Spot', 'Corn_healthy', 
    'Corn_Northern_Leaf_Blight', 'Grape_Black_Rot', 'Grape_Esca_Black_Measles', 
    'Grape_healthy', 'Grape_Leaf_Blight_Isariopsis', 'Orange_Haunglongbing_Citrus_Greening', 
    'Peach_Bacterial_Spot', 'Peach_healthy', 'Pepper_Bell_Bacterial_Spot', 
    'Pepper_Bell_healthy', 'Potato_Early_Blight', 'Potato_healthy', 
    'Potato_Late_Blight', 'Raspberry_healthy', 'Soybean_healthy', 
    'Squash_Powdery_Mildew', 'Strawberry_healthy', 'Strawberry_Leaf_Scorch', 
    'Tomato_Bacterial_Spot', 'Tomato_Early_Blight', 'Tomato_healthy', 
    'Tomato_Late_Blight', 'Tomato_Leaf_Mold', 'Tomato_Mosaic_Virus', 
    'Tomato_Septoria_Leaf_Spot', 'Tomato_Target_Spot', 'Tomato_Two_Spotted_Spider_Mite', 
    'Tomato_Yellow_Leaf_Curl_Virus', 'Wheat_Crown_and_Root_Rot', 'Wheat_healthy', 
    'Wheat_Leaf_Rust', 'Wheat_Loose_Smut'
]
CLASS_NAMES = sorted(raw_classes)
NUM_CLASSES = len(CLASS_NAMES)

IS_TRAINING = False 

app = Flask(__name__)

# ================= 2. 模型结构与加载 =================

def load_network_structure():
    """构造resnet50并在最后全连接层匹配类别数"""
    net = resnet50(weights=None)
    num_ftrs = net.fc.in_features
    net.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)
    return net

def init_model():
    """初始化模型加载，如果权重加载失败直接停止程序"""
    net = load_network_structure()
    
    # 优先加载重训练后的最优模型，否则加载初始模型
    if os.path.exists(BEST_MODEL_PATH):
        weights_to_load = BEST_MODEL_PATH
        print(f"📈 发现重训练权重: {BEST_MODEL_PATH}")
    else:
        weights_to_load = MODEL_PATH
        print(f"📦 加载初始权重: {MODEL_PATH}")

    if not os.path.exists(weights_to_load):
        print(f"❌ 严重错误: 找不到任何权重文件于 {weights_to_load}")
        sys.exit(1)

    try:
        # strict=True 保证网络层必须完全匹配
        state_dict = torch.load(weights_to_load, map_location=DEVICE)
        net.load_state_dict(state_dict, strict=True)
        net.to(DEVICE)
        net.eval()
        print(f"✅ 模型加载成功！当前设备: {DEVICE}")
        return net
    except Exception as e:
        print(f"🚨 权重加载失败(可能是类别数不匹配): {e}")
        sys.exit(1)

# 全局初始化
model = init_model()

# 预处理保持与训练一致 (ImageNet标准)
inference_transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

train_transform = T.Compose([
    T.RandomResizedCrop(224),
    T.RandomHorizontalFlip(),
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ================= 3. 辅助功能 =================

def get_feedback_count():
    count = 0
    for root, dirs, files in os.walk(FEEDBACK_DIR):
        count += len([f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))])
    return count

def train_task_thread():
    global IS_TRAINING, model
    print("\n🚀 后台训练任务开始...")
    IS_TRAINING = True
    
    try:
        # A. 检查数据
        if not os.path.exists(ORIGINAL_DATASET_DIR):
            print(f"❌ 错误: 原始训练集目录不存在 {ORIGINAL_DATASET_DIR}")
            return

        original_dataset = datasets.ImageFolder(ORIGINAL_DATASET_DIR, transform=train_transform)
        feedback_dataset = datasets.ImageFolder(FEEDBACK_DIR, transform=train_transform)
        combined_dataset = ConcatDataset([original_dataset, feedback_dataset])
        
        # 建议 batch_size 不要太大
        train_loader = DataLoader(combined_dataset, batch_size=32, shuffle=True, num_workers=4) 
        
        # B. 准备模型（在当前权重基础上继续练）
        new_model = load_network_structure()
        new_model.load_state_dict(model.state_dict())
        new_model.to(DEVICE)
        new_model.train()

        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(new_model.parameters(), lr=0.00001) # 用更小的学习率防止破坏权重

        EPOCHS = 3
        for epoch in range(EPOCHS):
            running_loss = 0.0
            for inputs, labels in train_loader:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                optimizer.zero_grad()
                outputs = new_model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
            print(f"   Epoch {epoch+1}/{EPOCHS} - Loss: {running_loss/len(train_loader):.4f}")

        # C. 保存与同步
        torch.save(new_model.state_dict(), BEST_MODEL_PATH)
        model.load_state_dict(new_model.state_dict())
        model.eval()

        # D. 归档数据
        archive_dest = os.path.join(ARCHIVE_DIR, str(int(time.time())))
        shutil.move(FEEDBACK_DIR, archive_dest)
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        print(f"📦 训练完成，模型已更新，反馈数据已归档。")

    except Exception as e:
        print(f"❌ 训练任务失败: {e}")
    finally:
        IS_TRAINING = False

# ================= 4. API 路由 =================

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    
    try:
        image = Image.open(io.BytesIO(file.read())).convert('RGB')
        img_tensor = inference_transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            outputs = model(img_tensor)
            # 调试：打印原始 Logits，观察是否某一项特别突出
            # print(f"Logits: {outputs.cpu().numpy()}") 
            
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)

        result_class = CLASS_NAMES[predicted_idx.item()]
        conf_score = confidence.item()

        print(f"🔍 预测结果: {result_class} (置信度: {conf_score:.4f})")

        return jsonify({
            'prediction': {
                'class_name': result_class,
                'confidence': float(f"{conf_score:.4f}")
            },
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def save_feedback():
    if 'file' not in request.files or 'correct_label' not in request.form:
        return jsonify({"error": "Missing parameter"}), 400

    file = request.files['file']
    label = request.form['correct_label']
    
    if label not in CLASS_NAMES:
        return jsonify({"error": f"Invalid label: {label}"}), 400

    try:
        label_dir = os.path.join(FEEDBACK_DIR, label)
        os.makedirs(label_dir, exist_ok=True)
        file.save(os.path.join(label_dir, f"{uuid.uuid4()}.jpg"))
        
        count = get_feedback_count()
        return jsonify({
            "status": "success", 
            "current_count": count,
            "ready_to_train": count >= RETRAIN_THRESHOLD
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/retrain', methods=['POST'])
def manual_retrain():
    if IS_TRAINING: return jsonify({"error": "Training in progress"}), 409
    if get_feedback_count() == 0: return jsonify({"error": "No data"}), 400
    
    threading.Thread(target=train_task_thread).start()
    return jsonify({"message": "Retraining started"})

@app.route('/status', methods=['GET'])
def server_status():
    return jsonify({
        "is_training": IS_TRAINING,
        "feedback_count": get_feedback_count(),
        "device": str(DEVICE)
    })

if __name__ == '__main__':
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    print(f"🚀 AI Server 运行于端口 {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
