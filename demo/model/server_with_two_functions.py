import os
import io
import uuid
import threading
import torch
import shutil
import torchvision.transforms as T
from torchvision import datasets
from torch.utils.data import DataLoader, ConcatDataset, Dataset
from torchvision.models import resnet50
from flask import Flask, request, jsonify
from PIL import Image
import time
import sys
import base64
import numpy as np
import cv2

# 尝试导入 GPU 监控库 (如果安装失败也不影响主程序运行)
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_GPU_MONITOR = True
except Exception as e:
    HAS_GPU_MONITOR = False
    print(f"⚠️ GPU Monitor disabled (nvidia-ml-py3 not found): {e}")

# ================= 1. 全局配置 =================
BASE_DIR = '/home/hzcu/repo/modelStaff'
# 权重路径
MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_v1.pth')      
BEST_MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_best.pth') 
# 数据路径
FEEDBACK_DIR = os.path.join(BASE_DIR, 'feedback_data')        
ARCHIVE_DIR = os.path.join(BASE_DIR, 'archived_feedback')     
ORIGINAL_DATASET_DIR = '/home/hzcu/PlantDiseases_Final_Split' 

RETRAIN_THRESHOLD = 1000
PORT = 5003  # 保持原端口，对接后端
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TASKS_DB = {}  # 全局字典，用于存储批量任务的状态

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

# ================= Grad-CAM 辅助函数 =================
def generate_gradcam(model, input_tensor, predicted_class):
    """生成 Grad-CAM 热力图"""
    # 获取最后一个卷积层的输出
    final_conv_layer = model.layer4[2]  # ResNet50 的最后一个卷积块

    # 存储梯度和激活
    gradients = []
    activations = []

    def forward_hook(module, input, output):
        activations.append(output)

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0])

    # 注册钩子
    forward_handle = final_conv_layer.register_forward_hook(forward_hook)
    backward_handle = final_conv_layer.register_backward_hook(backward_hook)

    # 前向传播
    output = model(input_tensor)
    predicted_output = output[0, predicted_class]

    # 反向传播
    model.zero_grad()
    predicted_output.backward()

    # 移除钩子
    forward_handle.remove()
    backward_handle.remove()

    # 获取梯度和激活
    gradients = gradients[0][0]  # gradients 是 batch_size x channels x h x w
    activations = activations[0][0]  # activations 同上

    # 计算 Grad-CAM
    weights = torch.mean(gradients, dim=[1, 2])  # 全局平均池化得到权重
    cam = torch.zeros(activations.shape[-2:], dtype=torch.float32)

    for i, w in enumerate(weights):
        cam += w * activations[i]

    cam = torch.nn.functional.relu(cam)  # ReLU 激活
    cam = cam - cam.min()
    cam = cam / cam.max()
    cam = cam.cpu().data.numpy()

    return cv2.resize(cam, (224, 224))  # 调整到原图大小

# ================= 辅助工具：GPU 监控 =================
def get_gpu_usage():
    """管理员专用：获取GPU显存和负载"""
    if not HAS_GPU_MONITOR or DEVICE.type != 'cuda':
        return "GPU: N/A"
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        used_mb = mem_info.used // 1024**2
        total_mb = mem_info.total // 1024**2
        return f"GPU: {util.gpu}% | Mem: {used_mb}/{total_mb} MB"
    except:
        return "GPU: Err"

# ================= 批量处理工具类 =================
class ImageFolderDataset(Dataset):
    """自定义 Dataset，用于读取文件夹中的图片"""
    def __init__(self, file_paths, transform):
        self.file_paths = file_paths
        self.transform = transform

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        path = self.file_paths[idx]
        try:
            image = Image.open(path).convert('RGB')
            return self.transform(image), path
        except Exception as e:
            print(f"⚠️ Reads error {path}: {e}")
            # 返回一个全0的tensor防止报错中断，后续可以根据path过滤
            return torch.zeros((3, 224, 224)), "ERROR_FILE"

def run_batch_inference(task_id, folder_path):
    """后台运行的批量预测逻辑（批量预测不添加热力图，以保持性能）"""
    print(f"[{task_id}] Thread started for: {folder_path}")
    
    # 1. 扫描文件
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(valid_exts)]
    total = len(all_files)
    
    if total == 0:
        TASKS_DB[task_id]['status'] = 'failed'
        TASKS_DB[task_id]['error'] = 'No images found in folder'
        return

    # 2. 策略选择 (Q3需求)
    batch_size = 32 if total >= 50 else 1
    num_workers = 4 if os.cpu_count() > 4 else 0
    
    print(f"[{task_id}] Strategy: Total={total}, BatchSize={batch_size}")

    dataset = ImageFolderDataset(all_files, inference_transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers)

    TASKS_DB[task_id].update({'total': total, 'processed': 0, 'status': 'processing'})
    
    results = []
    start_time = time.time()

    # 3. 开始预测
    with torch.no_grad():
        for batch_imgs, batch_paths in dataloader:
            batch_imgs = batch_imgs.to(DEVICE)
            
            outputs = model(batch_imgs)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidences, preds = torch.max(probs, 1)
            
            # 处理这一个 Batch 的结果
            current_batch_results = []
            for i in range(len(batch_paths)):
                path = batch_paths[i]
                if path == "ERROR_FILE": continue # 跳过损坏图片

                idx = preds[i].item()
                conf = confidences[i].item()
                
                res = {
                    "filename": os.path.basename(path),
                    "class_name": CLASS_NAMES[idx],
                    "confidence": float(f"{conf:.4f}")
                }
                current_batch_results.append(res)
            
            results.extend(current_batch_results)
            
            # 更新全局进度
            processed = len(results)
            elapsed = time.time() - start_time
            avg_per_img = elapsed / processed if processed > 0 else 0
            eta = (total - processed) * avg_per_img
            
            TASKS_DB[task_id].update({
                'processed': processed,
                'progress_percent': int((processed / total) * 100),
                'eta_seconds': int(eta),
                'avg_latency_ms': int(avg_per_img * 1000)
            })
            
            # 管理员日志 (Q1 & Q4)
            gpu_log = get_gpu_usage()
            print(f"[{task_id}] {processed}/{total} ({int(processed/total*100)}%) | ETA: {int(eta)}s | {gpu_log}")

    # 4. 完成
    TASKS_DB[task_id]['status'] = 'completed'
    TASKS_DB[task_id]['results'] = results # 这里存了所有结果
    # 注意：如果 results 极大(几十万条)，建议直接写入 json 文件到硬盘，而不是存在内存里
    print(f"[{task_id}] Finished in {int(time.time() - start_time)}s")


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

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "up", "device": str(DEVICE), "mode": "Merged"})

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    
    try:
        image = Image.open(io.BytesIO(file.read())).convert('RGB')
        
        # 保存原始图像用于热力图叠加
        original_image = np.array(image.resize((224, 224)))  # ResNet 输入是 224x224，但原图调整为匹配
        
        img_tensor = inference_transform(image).unsqueeze(0).to(DEVICE)
        
        # 前向传播计算预测
        outputs = model(img_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        confidence, predicted_idx = torch.max(probabilities, 1)
        
        conf_score = confidence.item()
        result_class = CLASS_NAMES[predicted_idx.item()]
        
        # 低置信度拦截：如果置信度低于 0.6，返回模糊结果
        if conf_score < 0.6:
            print(f"🔍 预测结果: 低置信度 - 无法确定 (置信度: {conf_score:.4f})")
            return jsonify({
                'prediction': {
                    'class_name': "无法确定",
                    'confidence': float(f"{conf_score:.4f}")
                },
                'status': 'success',
                'explanation': {
                    'message': '模型预测置信度较低，建议重新拍摄更清晰的图像或咨询专家。',
                    'suggested_actions': ['重新拍摄照片', '使用放大镜', '求助农业专家']
                }
            })
        
        # 如果置信度足够高，则生成 Grad-CAM 热力图
        heat_map = generate_gradcam(model, img_tensor, predicted_idx.item())
        
        # 叠加热力图到原图
        heat_map = cv2.applyColorMap(np.uint8(255 * heat_map), cv2.COLORMAP_JET)
        superimposed_image = cv2.addWeighted(heat_map, 0.4, original_image, 0.6, 0)
        
        # 将叠加图像转换为 base64
        _, buffer = cv2.imencode('.jpg', superimposed_image)
        heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
        
        print(f"🔍 预测结果: {result_class} (置信度: {conf_score:.4f})")

        return jsonify({
            'prediction': {
                'class_name': result_class,
                'confidence': float(f"{conf_score:.4f}")
            },
            'status': 'success',
            'explanation': {
                'heatmap_image': f"data:image/jpeg;base64,{heatmap_base64}",
                'message': f'模型主要关注图像中的高亮区域来识别为“{result_class}”。',
                'suggested_actions': ['检查高亮区域是否有病斑', '确认环境下状况']
            }
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
        "ready_to_train": get_feedback_count() >= RETRAIN_THRESHOLD,
        "device": str(DEVICE)
    })

# --- 新增：批量任务接口 ---
@app.route('/batch/start', methods=['POST'])
def start_batch_task():
    """Java 上传 Zip 解压后，调用此接口开始预测"""
    data = request.json
    folder_path = data.get('folder_path')
    task_id = data.get('task_id')
    
    if not folder_path or not task_id:
        return jsonify({"error": "Missing folder_path or task_id"}), 400
    
    if not os.path.exists(folder_path):
        return jsonify({"error": "Folder does not exist"}), 404

    # 初始化状态
    TASKS_DB[task_id] = {'status': 'pending', 'processed': 0, 'total': 0}
    
    # 启动后台线程
    t = threading.Thread(target=run_batch_inference, args=(task_id, folder_path))
    t.start()
    
    return jsonify({"status": "started", "task_id": task_id})

@app.route('/batch/status/<task_id>', methods=['GET'])
def get_batch_status(task_id):
    """前端轮询此接口获取进度条"""
    task = TASKS_DB.get(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
        
    response = {
        "status": task['status'],
        "progress": task.get('progress_percent', 0),
        "metrics": {
            "processed": task.get('processed', 0),
            "total": task.get('total', 0),
            "eta_seconds": task.get('eta_seconds', 0),
            "avg_latency_ms": task.get('avg_latency_ms', 0)
        }
    }
    
    # 只有当任务完成时，才返回结果数据 (避免轮询时传输数据过大)
    if task['status'] == 'completed':
        response['results'] = task.get('results', [])
        
    return jsonify(response)

if __name__ == '__main__':
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    print(f"🚀 AI Server (Merged with Confidence Gate and Grad-CAM) 运行于端口 {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
