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
import traceback

# 尝试导入 GPU 监控库
try:
    import pynvml
    pynvml.nvmlInit()
    HAS_GPU_MONITOR = True
except Exception as e:
    HAS_GPU_MONITOR = False
    print(f"⚠️ GPU Monitor disabled: {e}")

# ================= 1. 全局配置 =================
BASE_DIR = '/home/hzcu/repo/modelStaff'
MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_v1.pth')      
BEST_MODEL_PATH = os.path.join(BASE_DIR, 'ResNet50_best.pth') 
FEEDBACK_DIR = os.path.join(BASE_DIR, 'feedback_data')        
ARCHIVE_DIR = os.path.join(BASE_DIR, 'archived_feedback')     
ORIGINAL_DATASET_DIR = '/home/hzcu/PlantDiseases_Final_Split' 

RETRAIN_THRESHOLD = 1000
PORT = 5001  
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

TASKS_DB = {}  
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
    net = resnet50(weights=None)
    num_ftrs = net.fc.in_features
    net.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)
    return net

def init_model():
    net = load_network_structure()
    weights_to_load = BEST_MODEL_PATH if os.path.exists(BEST_MODEL_PATH) else MODEL_PATH
    if not os.path.exists(weights_to_load):
        print(f"❌ 严重错误: 找不到任何权重文件于 {weights_to_load}")
        sys.exit(1)
    try:
        state_dict = torch.load(weights_to_load, map_location=DEVICE)
        net.load_state_dict(state_dict, strict=True)
        net.to(DEVICE)
        net.eval()
        print(f"✅ 模型加载成功！当前设备: {DEVICE}")
        return net
    except Exception as e:
        print(f"🚨 权重加载失败: {e}")
        sys.exit(1)

model = init_model()

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

# ================= Grad-CAM 修复版辅助函数 =================
def generate_gradcam(model, input_tensor, predicted_class):
    """生成 Grad-CAM 热力图 (修复了 Hook 警告和 CPU/GPU 设备问题)"""
    target_layer = model.layer4[2]
    gradients = []
    activations = []

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0].detach())

    def forward_hook(module, input, output):
        activations.append(output.detach())

    # 兼容新版 PyTorch 的 Hook 注册
    if hasattr(target_layer, 'register_full_backward_hook'):
        h_b = target_layer.register_full_backward_hook(backward_hook)
    else:
        h_b = target_layer.register_backward_hook(backward_hook)
    h_f = target_layer.register_forward_hook(forward_hook)

    # 计算梯度
    input_tensor.requires_grad = True
    model.zero_grad()
    output = model(input_tensor)
    score = output[0, predicted_class]
    score.backward()

    h_b.remove()
    h_f.remove()

    # 提取特征和梯度并转到 CPU
    grads = gradients[0][0].cpu().data.numpy()
    f_maps = activations[0][0].cpu().data.numpy()

    # 计算权重和热力图
    weights = np.mean(grads, axis=(1, 2))
    cam = np.zeros(f_maps.shape[1:], dtype=np.float32)
    for i, w in enumerate(weights):
        cam += w * f_maps[i]

    cam = np.maximum(cam, 0) # ReLU
    if np.max(cam) != 0:
        cam = cam / np.max(cam)
    
    return cv2.resize(cam, (224, 224))

# ================= 辅助工具：GPU 监控 =================
def get_gpu_usage():
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

# ================= 批量处理 =================
class ImageFolderDataset(Dataset):
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
        except:
            return torch.zeros((3, 224, 224)), "ERROR_FILE"

def run_batch_inference(task_id, folder_path):
    all_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
    total = len(all_files)
    if total == 0:
        TASKS_DB[task_id]['status'] = 'failed'
        return
    
    batch_size = 32 if total >= 50 else 1
    dataloader = DataLoader(ImageFolderDataset(all_files, inference_transform), batch_size=batch_size)
    TASKS_DB[task_id].update({'total': total, 'processed': 0, 'status': 'processing'})
    
    results = []
    start_time = time.time()
    with torch.no_grad():
        for batch_imgs, batch_paths in dataloader:
            batch_imgs = batch_imgs.to(DEVICE)
            outputs = model(batch_imgs)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidences, preds = torch.max(probs, 1)
            for i in range(len(batch_paths)):
                if batch_paths[i] == "ERROR_FILE": continue
                results.append({
                    "filename": os.path.basename(batch_paths[i]),
                    "class_name": CLASS_NAMES[preds[i].item()],
                    "confidence": float(f"{confidences[i].item():.4f}")
                })
            TASKS_DB[task_id].update({'processed': len(results), 'progress_percent': int((len(results)/total)*100)})
    
    TASKS_DB[task_id].update({'status': 'completed', 'results': results})

# ================= 4. API 路由 =================

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    
    try:
        # 读取图片
        raw_data = file.read()
        image = Image.open(io.BytesIO(raw_data)).convert('RGB')
        original_image = np.array(image.resize((224, 224)))
        
        # 1. 正常推理 (不计算梯度，保证速度)
        img_tensor = inference_transform(image).unsqueeze(0).to(DEVICE)
        with torch.no_grad():
            outputs = model(img_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probs, 1)
        
        conf_score = confidence.item()
        result_class = CLASS_NAMES[predicted_idx.item()]
        
        # 低置信度拦截
        if conf_score < 0.6:
            return jsonify({
                'prediction': {'class_name': "无法确定", 'confidence': float(f"{conf_score:.4f}")},
                'status': 'success',
                'explanation': {
                    'heatmap_image': 'fault', 
                    'message': '置信度较低，建议重新拍摄清晰照片。'
                }
            })
        
        # 2. 高置信度：生成热力图 (单独触发一次带梯度的前向传播)
        heatmap_base64 = None
        try:
            # 开启梯度算热力图
            cam = generate_gradcam(model, img_tensor, predicted_idx.item())
            cam_color = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
            
            # 颜色空间整理 OpenCV (BGR) -> Display (RGB)
            cam_rgb = cv2.cvtColor(cam_color, cv2.COLOR_BGR2RGB)
            superimposed = cv2.addWeighted(cam_rgb, 0.4, original_image, 0.6, 0)
            
            # 转回 BGR 供 cv2.imencode 正常工作
            final_bgr = cv2.cvtColor(superimposed, cv2.COLOR_RGB2BGR)
            _, buffer = cv2.imencode('.jpg', final_bgr)
            heatmap_base64 = base64.b64encode(buffer).decode('utf-8')
        except Exception as cam_ex:
            print(f"Heatmap failed: {cam_ex}")

        return jsonify({
            'prediction': {'class_name': result_class, 'confidence': float(f"{conf_score:.4f}")},
            'status': 'success',
            'explanation': {
                'heatmap_image': f"data:image/jpeg;base64,{heatmap_base64}" if heatmap_base64 else 'fault',
                'message': f'检测到：{result_class}。',
                'suggested_actions': ['检查高亮区域', '对比典型病症']
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/feedback', methods=['POST'])
def save_feedback():
    if 'file' not in request.files or 'correct_label' not in request.form:
        return jsonify({"error": "Missing parameter"}), 400
    file = request.files['file']
    label = request.form['correct_label']
    if label not in CLASS_NAMES: return jsonify({"error": "Invalid label"}), 400
    try:
        label_dir = os.path.join(FEEDBACK_DIR, label)
        os.makedirs(label_dir, exist_ok=True)
        file.save(os.path.join(label_dir, f"{uuid.uuid4()}.jpg"))
        return jsonify({"status": "success", "current_count": 0}) 
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/batch/start', methods=['POST'])
def start_batch_task():
    data = request.json
    folder_path, task_id = data.get('folder_path'), data.get('task_id')
    if not folder_path or not task_id: return jsonify({"error": "Missing info"}), 400
    TASKS_DB[task_id] = {'status': 'pending'}
    threading.Thread(target=run_batch_inference, args=(task_id, folder_path)).start()
    return jsonify({"status": "started", "task_id": task_id})

@app.route('/batch/status/<task_id>', methods=['GET'])
def get_batch_status(task_id):
    task = TASKS_DB.get(task_id)
    if not task: return jsonify({"error": "N/A"}), 404
    return jsonify(task)

if __name__ == '__main__':
    os.makedirs(FEEDBACK_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
