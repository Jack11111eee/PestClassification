# ==============================================================================
#  predict.py - 加载训练好的模型进行单张图片预测
# ==============================================================================
import os
import torch
import torchvision.transforms as T
from torchvision.models import resnet50
from PIL import Image
import json

# --- 1. 配置参数 ---
# 模型权重路径 (使用你训练好的那个!)
MODEL_PATH = '/home/hzcu/outcomes/ResNet50_v1.pth' 
# 数据集根目录 (用来获取类别名称)
# DATA_DIR = '/home/jovyan/notebook/Agri/PlantDiseases_Final_Split'
# 类别数量
NUM_CLASSES = 42
# 设备
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 2. 加载类别名称 ---
# ImageFolder会按字母顺序排序文件夹，所以我们直接用os.listdir并排序来模拟
# 确保这个顺序和训练时完全一致！
#class_names = sorted([d.name for d in os.scandir(os.path.join(DATA_DIR, 'train')) if d.is_dir()])
class_names = [
    'Apple_Black_Rot',
    'Apple_Cedar_Apple_Rust',
    'Apple_healthy',
    'Apple_Scab',
    'Blueberry_healthy',
    'Cherry_healthy',
    'Cherry_Powdery_Mildew',
    'Corn_Common_Rust',
    'Corn_Gray_Leaf_Spot',
    'Corn_healthy',
    'Corn_Northern_Leaf_Blight',
    'Grape_Black_Rot',
    'Grape_Esca_Black_Measles',
    'Grape_healthy',
    'Grape_Leaf_Blight_Isariopsis',
    'Orange_Haunglongbing_Citrus_Greening',
    'Peach_Bacterial_Spot',
    'Peach_healthy',
    'Pepper_Bell_Bacterial_Spot',
    'Pepper_Bell_healthy',
    'Potato_Early_Blight',
    'Potato_healthy',
    'Potato_Late_Blight',
    'Raspberry_healthy',
    'Soybean_healthy',
    'Squash_Powdery_Mildew',
    'Strawberry_healthy',
    'Strawberry_Leaf_Scorch',
    'Tomato_Bacterial_Spot',
    'Tomato_Early_Blight',
    'Tomato_healthy',
    'Tomato_Late_Blight',
    'Tomato_Leaf_Mold',
    'Tomato_Mosaic_Virus',
    'Tomato_Septoria_Leaf_Spot',
    'Tomato_Target_Spot',
    'Tomato_Two_Spotted_Spider_Mite',
    'Tomato_Yellow_Leaf_Curl_Virus',
    'Wheat_Crown_and_Root_Rot',
    'Wheat_healthy',
    'Wheat_Leaf_Rust',
    'Wheat_Loose_Smut',
]


# --- 3. 定义模型并加载权重 ---
# 必须使用和训练时完全一样的模型结构
model = resnet50(weights=None) # 注意：这里不加载预训练权重，因为我们要加载自己的权重
num_ftrs = model.fc.in_features
model.fc = torch.nn.Linear(num_ftrs, NUM_CLASSES)

# 加载我们训练好的模型参数
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.to(DEVICE)
model.eval()  # !!! 必须设置为评估模式 !!!

# --- 4. 定义图像预处理 ---
# 必须使用和验证/测试集完全相同的预处理流程！
transform = T.Compose([
    T.Resize(256),
    T.CenterCrop(224),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# --- 5. 编写预测函数 ---
def predict_image(image_path):
    """
    对单张图片进行预测
    :param image_path: 图片文件的路径
    :return: (预测的类别名称, 置信度)
    """
    try:
        # 加载并预处理图片
        image = Image.open(image_path).convert('RGB')
        image_tensor = transform(image).unsqueeze(0).to(DEVICE) # 增加一个batch维度

        # 不计算梯度，加快速度
        with torch.no_grad():
            outputs = model(image_tensor)
            # 使用softmax将输出转换为概率分布
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            # 找到概率最高的类别
            confidence, predicted_idx = torch.max(probabilities, 1)

        predicted_class = class_names[predicted_idx.item()]
        confidence_score = confidence.item()

        return predicted_class, confidence_score

    except Exception as e:
        return str(e), 0.0

# # --- 6. 主程序入口 (方便直接在命令行测试) ---
# if __name__ == '__main__':
#     test_image_path = '/home/hzcu/outcomes/3a4dd05d-a912-4c16-a679-f00028a0d7b6___FAM_B.Rot 5011.JPG' 

#     if not os.path.exists(test_image_path):
#         print(f"错误：测试图片路径不存在: {test_image_path}")
#         print("请修改 'test_image_path' 变量为你自己的图片路径。")
#     else:
#         print(f"正在对图片进行预测: {test_image_path}")
#         predicted_class, confidence = predict_image(test_image_path)
#         print("="*30)
#         print(f"预测结果: {predicted_class}")
#         print(f"置信度: {confidence:.2%}")
#         print("="*30)