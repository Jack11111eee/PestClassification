# ==============================================================================
#  app.py - Flask后端API服务
# ==============================================================================
import os
import uuid
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

# 从我们自己的模块中导入预测函数
from predict import predict_image, class_names

# --- 1. 初始化 Flask App ---
app = Flask(__name__)

class_names = [
    'Apple_Black_Rot', 'Apple_Cedar_Apple_Rust', 'Apple_healthy', 'Apple_Scab', 'Blueberry_healthy',
    'Cherry_healthy', 'Cherry_Powdery_Mildew', 'Corn_Common_Rust', 'Corn_Gray_Leaf_Spot', 'Corn_healthy',
    'Corn_Northern_Leaf_Blight', 'Grape_Black_Rot', 'Grape_Esca_Black_Measles', 'Grape_healthy',
    'Grape_Leaf_Blight_Isariopsis', 'Orange_Haunglongbing_Citrus_Greening', 'Peach_Bacterial_Spot',
    'Peach_healthy', 'Pepper_Bell_Bacterial_Spot', 'Pepper_Bell_healthy', 'Potato_Early_Blight',
    'Potato_healthy', 'Potato_Late_Blight', 'Raspberry_healthy', 'Soybean_healthy', 'Squash_Powdery_Mildew',
    'Strawberry_healthy', 'Strawberry_Leaf_Scorch', 'Tomato_Bacterial_Spot', 'Tomato_Early_Blight',
    'Tomato_healthy', 'Tomato_Late_Blight', 'Tomato_Leaf_Mold', 'Tomato_Mosaic_Virus',
    'Tomato_Septoria_Leaf_Spot', 'Tomato_Target_Spot', 'Tomato_Two_Spotted_Spider_Mite',
    'Tomato_Yellow_Leaf_Curl_Virus', 'Wheat_Crown_and_Root_Rot', 'Wheat_healthy', 'Wheat_Leaf_Rust',
    'Wheat_Loose_Smut',
]
chinese_class_names = [
    "苹果黑腐病", "苹果雪松锈病", "苹果 - 健康", "苹果黑星病", "蓝莓 - 健康", "樱桃 - 健康", "樱桃白粉病",
    "玉米普通锈病", "玉米灰斑病", "玉米 - 健康", "玉米大斑病（北方叶枯病）", "葡萄黑腐病", "葡萄埃斯卡病（黑麻疹病）",
    "葡萄 - 健康", "葡萄叶枯病（伊斯 ariopsis 属）", "柑橘黄龙病", "桃细菌性斑点病", "桃 - 健康",
    "甜椒细菌性斑点病", "甜椒 - 健康", "马铃薯早疫病", "马铃薯 - 健康", "马铃薯晚疫病", "树莓 - 健康",
    "大豆 - 健康", "南瓜白粉病", "草莓 - 健康", "草莓叶焦病", "番茄细菌性斑点病", "番茄早疫病",
    "番茄 - 健康", "番茄晚疫病", "番茄叶霉病", "番茄花叶病毒病", "番茄 Septoria 叶斑病", "番茄靶斑病",
    "番茄二斑叶螨", "番茄黄化曲叶病毒病", "小麦冠根腐病", "小麦 - 健康", "小麦叶锈病", "小麦散黑穗病"
]
CH_TO_EN_MAP = dict(zip(chinese_class_names, class_names))

# --- 2. 配置 ---
# 设置一个用于临时保存上传文件的文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 允许上传的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    """检查文件后缀是否合法"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

print("✅ Flask App initialized. Ready to receive requests.")
# 提示：模型和类别等已经在 predict.py 被导入时加载好了，这里无需重复加载。

# --- 3. 创建API路由 ---

@app.route('/')
def index():
    """一个简单的欢迎页面，用于测试服务是否启动"""
    return "<h1>植物病害识别API已启动</h1><p>请使用POST方法向 /predict 接口上传图片。</p>"

@app.route('/predict', methods=['POST'])
def handle_prediction():
    """处理图片上传和预测的核心函数"""
    
    # --- A. 检查请求中是否包含文件 ---
    if 'file' not in request.files:
        return jsonify({'error': '请求中未找到文件部分(file part not found in request)'}), 400
    
    file = request.files['file']

    # --- B. 检查文件名 ---
    if file.filename == '':
        return jsonify({'error': '未选择文件(no file selected)'}), 400
        
    # --- C. 检查文件类型并保存 ---
    if file and allowed_file(file.filename):
        # 使用 werkzeug 的 secure_filename 防止恶意文件名
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        print(f"📄 文件已接收并保存: {filepath}")

        # --- D. 调用模型进行预测 ---
        try:
            print("🧠 正在调用模型进行预测...")
            predicted_class, confidence = predict_image(filepath)
            print(f"✅ 预测完成: {predicted_class}, 置信度: {confidence:.2%}")

            # --- E. 准备并返回JSON结果 ---
            result = {
                'prediction': {
                    'class_name': predicted_class,
                    'confidence': float(f"{confidence:.4f}") # 格式化为4位小数的浮点数
                },
                'model_info': {
                    'total_classes': len(class_names)
                }
            }
            return jsonify(result), 200

        except Exception as e:
            print(f"❌ 预测过程中发生错误: {e}")
            return jsonify({'error': f'预测失败: {str(e)}'}), 500
        
        finally:
            # --- F. (可选) 清理上传的文件 ---
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ 已清理临时文件: {filepath}")

    else:
        return jsonify({'error': '文件类型不被允许(file type not allowed)'}), 400
        
# 创建一个专门存放反馈数据的文件夹
FEEDBACK_FOLDER = '/home/hzcu/outcomes/feedback_data'
os.makedirs(FEEDBACK_FOLDER, exist_ok=True)
@app.route('/feedback', methods=['POST'])
def receive_feedback():
    """
    接收用户纠错后的数据
    """
    # 检查请求中是否包含文件和正确的标签
    if 'file' not in request.files or 'correct_label' not in request.form:
        return jsonify({"error": "请求不完整，需要'file'和'correct_label'两个字段"}), 400
    file = request.files['file']
    correct_label = request.form['correct_label']
    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400
    if file and correct_label:
        try:
            # 1. 根据正确的标签，创建对应的子文件夹 (如果不存在)
            label_folder = os.path.join(FEEDBACK_FOLDER, correct_label)
            os.makedirs(label_folder, exist_ok=True)
            # 2. 为了防止文件名冲突，生成一个唯一的文件名
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = str(uuid.uuid4()) + file_extension
            save_path = os.path.join(label_folder, unique_filename)
            
            # 3. 保存图片到指定文件夹
            file.save(save_path)
            print(f"收到新的反馈数据: 类别 '{correct_label}', 已保存至 '{save_path}'")
            return jsonify({"status": "success", "message": "感谢您的反馈！"}), 200
        except Exception as e:
            return jsonify({"error": f"处理反馈时出错: {str(e)}"}), 500
    return jsonify({"error": "未知错误"}), 500

# --- 4. 启动服务 ---
if __name__ == '__main__':
    # host='0.0.0.0' 让服务可以被外部访问
    # port=5000 是Flask默认端口，可以修改
    app.run(host='0.0.0.0', port=8000, debug=True)
    # 注意：debug=True 模式下，每次代码改动服务会自动重启，方便开发。
    # 真正部署时应设为 debug=False。
