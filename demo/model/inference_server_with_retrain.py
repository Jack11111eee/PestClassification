# inference_server_with_retrain.py
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
MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_v1.pth')      # 初始模型
BEST_MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_best.pth') # 用于保存新训练的最好模型
FEEDBACK_DIR = os.path.join(BASE_DIR, 'feedback_data')        # 待训练数据池
ARCHIVE_DIR = os.path.join(BASE_DIR, 'archived_feedback')     # 训练完归档的数据

# 必须指向你服务器上的原始大数据集路径 (用于防止遗忘旧知识)
ORIGINAL_DATASET_DIR = '/home/hzcu/PlantDiseases_Final_Split' 

# 阈值配置
RETRAIN_THRESHOLD = 5  # 为了方便测试，建议先设为 5。测试没问题后再改成 100
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
    """定义网络结构，方便复用"""
    net = resnet50(weights=None)
    num_ftrs = net.fc.in_features
    net.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)
    return net

print(f"🔄 初始化加载模型...")
model = load_network_structure()
# 优先加载 Best 模型（如果有），否则加载初始 v1 模型
current_weights = BEST_MODEL_PATH if os.path.exists(BEST_MODEL_PATH) else MODEL_PATH
try:
    model.load_state_dict(torch.load(current_weights, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    print(f"✅ 模型加载成功: {current_weights}")
except Exception as e:
    print(f"❌ 模型加载失败: {e}")

# 预处理 (保持训练和推理一致)
inference_transform = T.Compose([
    T.Resize(256),T.CenterCrop(224),T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
train_transform = T.Compose([
    T.RandomResizedCrop(224),T.RandomHorizontalFlip(),T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# ================= 3. 后台训练逻辑 (核心) =================

def train_task_thread():
    """后台训练线程函数"""
    global IS_TRAINING, model
    print("\n🚀 [Background] 触发重训练任务 started...")
    IS_TRAINING = True
    
    try:
        # A. 准备数据
        # 1. 原始数据集
        original_dataset = datasets.ImageFolder(ORIGINAL_DATASET_DIR, transform=train_transform)
        # 2. 反馈数据集 (本次积攒的100张)
        feedback_dataset = datasets.ImageFolder(FEEDBACK_DIR, transform=train_transform)
        
        # 3. 混合数据 (防止遗忘)
        combined_dataset = ConcatDataset([original_dataset, feedback_dataset])
        train_loader = DataLoader(combined_dataset, batch_size=16, shuffle=True, num_workers=0) 
        # 注意: num_workers=0 是为了防止多进程在Flask中报错，虽然会慢一点但更稳
        
        # B. 准备新模型进行训练
        # 这是一个技巧：我们复制当前模型的参数作为起点，而不是从头随机初始化
        new_model = load_network_structure()
        new_model.load_state_dict(model.state_dict()) # 继承当前“智慧”
        new_model.to(DEVICE)
        new_model.train()

        criterion = torch.nn.CrossEntropyLoss()
        # 学习率设小一点 (LR=0.0001)，因为只是微调，不想大幅震荡
        optimizer = torch.optim.Adam(new_model.parameters(), lr=0.0001)

        print(f"📉 [Background] 开始训练，总数据量: {len(combined_dataset)}，计划训练 3 Epochs...")
        
        # C. 训练循环 (简化版，只跑3-5轮即可)
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
                
                if steps % 10 == 0:
                    print(f"   [Epoch {epoch+1}] Step {steps}, Loss: {loss.item():.4f}")
            
            print(f"✅ [Epoch {epoch+1} Done] Avg Loss: {running_loss/steps:.4f}")

        # D. 保存新模型
        torch.save(new_model.state_dict(), BEST_MODEL_PATH)
        print(f"💾 [Background] 新模型已保存至: {BEST_MODEL_PATH}")

        # E. 热更新 (Hot Reload) !!! 核心代码 !!!
        # 在主线程使用新模型之前，我们在内存中直接替换变量
        model.load_state_dict(new_model.state_dict())
        model.eval()
        print("🔄 [Background] 全局模型引用已指向新训练的权重 (Hot Reload Completed!)")

        # F. 数据归档 (可选)
        # 训练完了，把 feedback_data 里的图片移到 archive 去，清空计数器
        timestamp = int(time.time())
        archive_dest = os.path.join(ARCHIVE_DIR, str(timestamp))
        shutil.move(FEEDBACK_DIR, archive_dest)
        os.makedirs(FEEDBACK_DIR, exist_ok=True) # 重建空目录
        print(f"📦 [Background] 反馈数据已归档至 {archive_dest}")

    except Exception as e:
        print(f"❌ [Background] 训练任务出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        IS_TRAINING = False
        print("🏁 [Background] 训练任务结束。\n")

def check_and_trigger_retrain():
    """检查是否满足训练条件"""
    if IS_TRAINING:
        print("⚠️ 正在训练中，跳过本次触发检查。")
        return

    # 统计 feedback_data 文件夹下的所有图片数量
    count = 0
    for root, dirs, files in os.walk(FEEDBACK_DIR):
        count += len([f for f in files if f.endswith(('.jpg', '.png', '.jpeg'))])
    
    print(f"📊 当前反馈池积累图片数: {count} / 阈值: {RETRAIN_THRESHOLD}")
    
    if count >= RETRAIN_THRESHOLD:
        # 启动新线程
        t = threading.Thread(target=train_task_thread)
        t.start()
        return True
    return False

# ================= 4. API 路由 =================

@app.route('/predict', methods=['POST'])
def predict():
    """
    接收图片流 -> 内存处理 -> 预测 -> 返回JSON
    注意：这里不再保存临时文件到 uploads 文件夹，速度更快
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        # A. 读取文件到内存
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        
        # B. 预处理
        img_tensor = transform(image).unsqueeze(0).to(DEVICE)
        
        # C. 推理
        with torch.no_grad():
            outputs = model(img_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)

        result_class = CLASS_NAMES[predicted_idx.item()]
        confidence_score = float(confidence.item())

        # D. 返回结果
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
        
    # 记得引用全局的 model (它可能会被后台线程更新)
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        img_tensor = inference_transform(image).unsqueeze(0).to(DEVICE)
        
        with torch.no_grad():
            outputs = model(img_tensor) # 这里调用的 model 总是最新的
            probs = torch.nn.functional.softmax(outputs, dim=1)
            conf, idx = torch.max(probs, 1)
            
        return jsonify({
            'prediction': {'class_name': CLASS_NAMES[idx.item()], 'confidence': float(conf.item())},
            'status': 'success',
            'model_version': 'latest' # 可以标记一下
        })
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def save_feedback():
    if 'file' not in request.files or 'correct_label' not in request.form:
        return jsonify({"error": "Missing info"}), 400
    
    file = request.files['file']
    correct_label = request.form['correct_label']
    
    if correct_label not in CLASS_NAMES:
        return jsonify({"error": "Invalid label"}), 400

    try:
        # 保存图片
        label_dir = os.path.join(FEEDBACK_DIR, correct_label)
        os.makedirs(label_dir, exist_ok=True)
        filename = f"{uuid.uuid4()}.jpg"
        file.save(os.path.join(label_dir, filename))
        
        # 重点：保存成功后，立即检查是否需要触发训练
        triggered = check_and_trigger_retrain()
        
        msg = "Feedback saved."
        if triggered:
            msg += " Retraining triggered in background!"
            
        return jsonify({"status": "success", "message": msg, "retraining": triggered})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def server_status():
    """查看服务器当前状态"""
    # 统计 feedback 数量
    count = 0
    for _, _, files in os.walk(FEEDBACK_DIR):
        count += len([f for f in files if f.endswith(('.jpg', '.png'))])
        
    return jsonify({
        "is_training": IS_TRAINING,
        "feedback_count": count,
        "feedback_threshold": RETRAIN_THRESHOLD,
        "device": str(DEVICE)
    })

if __name__ == '__main__':
    # 初始化目录
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    
    print(f"🚀 AI Server Pro starting on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True) 
    # threaded=True 允许多个请求并发，防止训练时阻塞预测请求
