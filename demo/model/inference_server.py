# inference_server.py
import os
import io
import uuid
import torch
import torchvision.transforms as T
from torchvision.models import resnet50
from flask import Flask, request, jsonify
from PIL import Image

# ================= 配置区域 (请确认这里) =================
# 1. 模型路径
MODEL_PATH = '/home/hzcu/repo/modelStaff/ResNet50_v1.pth' 

# 2. 反馈数据保存路径 (用于后续重训练)
FEEDBACK_FOLDER = '/home/hzcu/repo/modelStaff/feedback_data'

# 3. 运行端口
PORT = 5001  # 建议用 5001，避免和正在运行的旧 Flask (5000) 冲突

# ================= 核心逻辑 =================
app = Flask(__name__)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 1. 类别定义 (必须与训练时一致) ---
# CLASS_NAMES = [
#     'Apple_Black_Rot', 'Apple_Cedar_Apple_Rust', 'Apple_healthy', 'Apple_Scab', 'Blueberry_healthy',
#     'Cherry_healthy', 'Cherry_Powdery_Mildew', 'Corn_Common_Rust', 'Corn_Gray_Leaf_Spot', 'Corn_healthy',
#     'Corn_Northern_Leaf_Blight', 'Grape_Black_Rot', 'Grape_Esca_Black_Measles', 'Grape_healthy',
#     'Grape_Leaf_Blight_Isariopsis', 'Orange_Haunglongbing_Citrus_Greening', 'Peach_Bacterial_Spot',
#     'Peach_healthy', 'Pepper_Bell_Bacterial_Spot', 'Pepper_Bell_healthy', 'Potato_Early_Blight',
#     'Potato_healthy', 'Potato_Late_Blight', 'Raspberry_healthy', 'Soybean_healthy', 'Squash_Powdery_Mildew',
#     'Strawberry_healthy', 'Strawberry_Leaf_Scorch', 'Tomato_Bacterial_Spot', 'Tomato_Early_Blight',
#     'Tomato_healthy', 'Tomato_Late_Blight', 'Tomato_Leaf_Mold', 'Tomato_Mosaic_Virus',
#     'Tomato_Septoria_Leaf_Spot', 'Tomato_Target_Spot', 'Tomato_Two_Spotted_Spider_Mite',
#     'Tomato_Yellow_Leaf_Curl_Virus', 'Wheat_Crown_and_Root_Rot', 'Wheat_healthy', 'Wheat_Leaf_Rust',
#     'Wheat_Loose_Smut',
# ]
# CLASS_NAMES.sort()
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

# --- 2. 加载模型 (Global Loading) ---
print(f"🔄 Loading model from {MODEL_PATH} on {DEVICE}...")

try:
    # 初始化模型结构
    model = resnet50(weights=None) 
    num_ftrs = model.fc.in_features
    model.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)
    
    # 加载权重
    state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval() # 开启评估模式
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("请检查路径是否正确！")

# --- 3. 预处理定义 ---
transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# ================= 接口定义 =================

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口，供 Spring Boot 检测 Python 服务是否存活"""
    return jsonify({"status": "up", "device": str(DEVICE)})

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

@app.route('/feedback', methods=['POST'])
def save_feedback():
    """
    保存用户反馈的数据，用于 retrain.py 训练
    """
    if 'file' not in request.files or 'correct_label' not in request.form:
        return jsonify({"error": "Missing file or correct_label"}), 400
    
    file = request.files['file']
    correct_label = request.form['correct_label']
    
    if correct_label not in CLASS_NAMES:
        # 这是一个很好的校验，防止用户乱传标签污染数据集
        return jsonify({"error": f"Invalid label. Must be one of {len(CLASS_NAMES)} classes."}), 400

    try:
        # 创建目录结构：feedback_data/Apple_Black_Rot/uuid.jpg
        label_dir = os.path.join(FEEDBACK_FOLDER, correct_label)
        os.makedirs(label_dir, exist_ok=True)
        
        # 生成唯一文件名
        ext = os.path.splitext(file.filename)[1] if '.' in file.filename else '.jpg'
        filename = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(label_dir, filename)
        
        file.save(save_path)
        print(f"📝 Feedback saved: {save_path}")
        
        return jsonify({"status": "success", "saved_path": save_path})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 生产环境建议 debug=False
    print(f"🚀 Inference Server starting on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False)
