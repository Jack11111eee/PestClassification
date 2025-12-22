# inference_server_manual.py
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

# ================= 1. 全局配置 =================
# 基础路径
BASE_DIR = '/home/hzcu/repo/modelStaff'
MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_v1.pth')      
BEST_MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_best.pth') 
FEEDBACK_DIR = os.path.join(BASE_DIR, 'feedback_data')        
ARCHIVE_DIR = os.path.join(BASE_DIR, 'archived_feedback')     

# 原始数据集路径
ORIGINAL_DATASET_DIR = '/home/hzcu/PlantDiseases_Final_Split' 

# 阈值配置
RETRAIN_THRESHOLD = 5  # 达到这个数后，提示管理员可以训练了
PORT = 5001
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 类别定义 (42类)
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

# 状态标志位
IS_TRAINING = False 

# ================= 2. 模型初始加载 =================
app = Flask(__name__)

def load_network_structure():
    net = resnet50(weights=None)
    num_ftrs = net.fc.in_features
    net.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)
    return net

print(f"🔄 初始化加载模型...")
model = load_network_structure()
current_weights = BEST_MODEL_PATH if os.path.exists(BEST_MODEL_PATH) else MODEL_PATH
try:
    model.load_state_dict(torch.load(current_weights, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    print(f"✅ 模型加载成功: {current_weights}")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")

# 预处理
inference_transform = T.Compose([
    T.Resize(256),T.CenterCrop(224),T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
train_transform = T.Compose([
    T.RandomResizedCrop(224),T.RandomHorizontalFlip(),T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ================= 3. 辅助函数 =================

def get_feedback_count():
    """统计当前反馈池的图片数量"""
    count = 0
    for root, dirs, files in os.walk(FEEDBACK_DIR):
        count += len([f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))])
    return count

def train_task_thread():
    """后台训练线程函数 - 逻辑不变"""
    global IS_TRAINING, model
    print("\n🚀 [Background] 管理员已触发重训练任务 started...")
    IS_TRAINING = True
    
    try:
        # A. 准备数据
        original_dataset = datasets.ImageFolder(ORIGINAL_DATASET_DIR, transform=train_transform)
        feedback_dataset = datasets.ImageFolder(FEEDBACK_DIR, transform=train_transform)
        combined_dataset = ConcatDataset([original_dataset, feedback_dataset])
        train_loader = DataLoader(combined_dataset, batch_size=16, shuffle=True, num_workers=0) 
        
        # B. 准备模型
        new_model = load_network_structure()
        new_model.load_state_dict(model.state_dict())
        new_model.to(DEVICE)
        new_model.train()

        criterion = torch.nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(new_model.parameters(), lr=0.0001)

        print(f"📉 [Background] 开始训练，总数据量: {len(combined_dataset)}...")
        
        # C. 训练循环
        EPOCHS = 3
        for epoch in range(EPOCHS):
            running_loss = 0.0
            steps = 0
            for inputs, labels in train_loader:
                inputs, labels = inputs.to(DEVICE), labels.to(DEVICE)
                optimizer.zero_grad()
                outputs = new_model(inputs)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
                running_loss += loss.item()
                steps += 1
            print(f"✅ [Epoch {epoch+1} Done] Avg Loss: {running_loss/steps:.4f}")

        # D. 保存
        torch.save(new_model.state_dict(), BEST_MODEL_PATH)
        print(f"💾 [Background] 新模型已保存至: {BEST_MODEL_PATH}")

        # E. 热更新
        model.load_state_dict(new_model.state_dict())
        model.eval()
        print("🔄 [Background] 全局模型热更新完成！")

        # F. 归档
        timestamp = int(time.time())
        archive_dest = os.path.join(ARCHIVE_DIR, str(timestamp))
        shutil.move(FEEDBACK_DIR, archive_dest)
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        print(f"📦 [Background] 反馈数据已归档至 {archive_dest}")

    except Exception as e:
        print(f"❌ [Background] 训练任务出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        IS_TRAINING = False
        print("🏁 [Background] 训练任务结束。\n")

# ================= 4. API 路由 =================

@app.route('/predict', methods=['POST'])
def predict():
    """预测接口 (已清理冗余代码)"""
    if 'file' not in request.files: return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No selected file'}), 400

    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        img_tensor = inference_transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)

        result_class = CLASS_NAMES[predicted_idx.item()]
        confidence_score = float(confidence.item())

        return jsonify({
            'prediction': {
                'class_name': result_class,
                'confidence': float(f"{confidence_score:.4f}")
            },
            'status': 'success'
        })
    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def save_feedback():
    """
    接收反馈 -> 保存图片 -> 返回当前是否达到训练条件
    注意：这里不再自动触发训练！
    """
    if 'file' not in request.files or 'correct_label' not in request.form:
        return jsonify({"error": "Missing info"}), 400
    file = request.files['file']
    correct_label = request.form['correct_label']
    if correct_label not in CLASS_NAMES:
        return jsonify({"error": "Invalid label"}), 400

    try:
        label_dir = os.path.join(FEEDBACK_DIR, correct_label)
        os.makedirs(label_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}.jpg"
        file.save(os.path.join(label_dir, filename))
        
        # 统计数量
        count = get_feedback_count()
        ready_to_train = count >= RETRAIN_THRESHOLD
        
        msg = f"Feedback saved. Total images: {count}"
        if ready_to_train:
            msg += " (Threshold reached! Waiting for admin to start training.)"
            
        return jsonify({
            "status": "success", 
            "message": msg, 
            "current_count": count,
            "threshold": RETRAIN_THRESHOLD,
            "ready_to_train": ready_to_train  # 前端通过这个字段判断是否让按钮变绿
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# [NEW] 新增的手动触发接口
@app.route('/retrain', methods=['POST'])
def manual_retrain():
    """
    管理员手动调用此接口开始训练
    """
    if IS_TRAINING:
        return jsonify({"status": "error", "message": "Training is already in progress!"}), 409
    
    count = get_feedback_count()
    
    # 你可以选择强制检查阈值，也可以允许管理员强制跑 (这里我写了逻辑允许强制跑，但给出警告)
    if count == 0:
        return jsonify({"status": "error", "message": "No feedback data to train on."}), 400
        
    # 启动后台线程
    t = threading.Thread(target=train_task_thread)
    t.start()
    
    return jsonify({
        "status": "success", 
        "message": "Retraining task started in background.",
        "data_count": count
    })

@app.route('/status', methods=['GET'])
def server_status():
    """查看状态"""
    count = get_feedback_count()
    return jsonify({
        "is_training": IS_TRAINING,
        "feedback_count": count,
        "feedback_threshold": RETRAIN_THRESHOLD,
        "ready_to_train": count >= RETRAIN_THRESHOLD
    })

if __name__ == '__main__':
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    print(f"🚀 AI Server (Manual Trigger) starting on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
