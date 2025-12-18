# inference_server_pro.py
# 这是一个增强版服务：支持单张预测 + 批量异步预测 + GPU监控 + 进度条
import os
import io
import time
import uuid
import threading
import torch
import torchvision.transforms as T
from torch.utils.data import Dataset, DataLoader
from torchvision.models import resnet50
from flask import Flask, request, jsonify
from PIL import Image

# 尝试导入 GPU 监控库 (如果安装失败也不影响主程序运行)
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_GPU_MONITOR = True
except Exception as e:
    HAS_GPU_MONITOR = False
    print(f"⚠️ GPU Monitor disabled (nvidia-ml-py3 not found): {e}")

# ================= 配置区域 =================
MODEL_PATH = '/home/hzcu/repo/modelStaff/ResNet50_v1.pth' 
FEEDBACK_FOLDER = '/home/hzcu/repo/modelStaff/feedback_data'
PORT = 5002  # 使用 5002 端口，避免冲突

# ================= 核心逻辑 =================
app = Flask(__name__)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TASKS_DB = {} # 全局字典，用于存储批量任务的状态

# --- 1. 类别定义 (保持与原版绝对一致) ---
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

# --- 2. 加载模型 ---
print(f"🔄 Loading model from {MODEL_PATH} on {DEVICE}...")
try:
    model = resnet50(weights=None) 
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)
    state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")

# --- 3. 预处理定义 ---
transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

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
    """后台运行的批量预测逻辑"""
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

    dataset = ImageFolderDataset(all_files, transform)
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


# ================= 接口定义 =================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "up", "device": str(DEVICE), "mode": "Pro"})

# --- 保持原有的单张预测接口 (兼容性) ---
@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    try:
        img_bytes = file.read()
        image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        img_tensor = transform(image).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            outputs = model(img_tensor)
            conf, pred = torch.max(torch.nn.functional.softmax(outputs, dim=1), 1)
        return jsonify({
            'prediction': {'class_name': CLASS_NAMES[pred.item()], 'confidence': float(conf.item())},
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 保持原有的反馈接口 ---
@app.route('/feedback', methods=['POST'])
def save_feedback():
    # ... (原有代码逻辑保持不变，为了节省篇幅这里省略，你自己贴过来或者这部分不需要改动) ...
    # 为了完整运行，建议这里直接复制原来 save_feedback 的内容
    pass 

# +++++++++++++++++ NEW: 批量任务接口 +++++++++++++++++

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
    print(f"🚀 INFERENCE PRO SERVER starting on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)
