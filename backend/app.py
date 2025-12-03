# backend/app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import jwt
import datetime
import os
from PIL import Image
import torch
from torchvision import transforms
from torchvision.models import resnet34  # 确保你的模型文件和 app.py 在同一目录下

app = Flask(__name__, static_folder='static')
CORS(app)  # 允许跨域请求

# --- 数据库和密钥配置 ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_super_secret_key'  # 建议使用更复杂的密钥
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# --- 数据库模型 ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    img_url = db.Column(db.String(200), nullable=False)
    prediction = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    is_correct = db.Column(db.Boolean, default=None)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    user = db.relationship('User', backref=db.backref('records', lazy=True))


# --- AI 模型加载 ---
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = resnet34(num_classes=5).to(device)
model_weight_path = "./weights/resNet34.pth"  # 你的模型权重路径
model.load_state_dict(torch.load(model_weight_path, map_location=device))
model.eval()
class_names = ['daisy', 'dandelion', 'roses', 'sunflowers', 'tulips'] # 替换成你的真实类别名

data_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# --- API 路由 ---

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'User already exists'}), 409
    
    new_user = User(username=data['username'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({'token': token})

@app.route('/api/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # AI 推理
        img = Image.open(filepath).convert('RGB')
        img_tensor = data_transform(img).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(img_tensor)
            _, predicted_idx = torch.max(outputs, 1)
            probabilities = torch.softmax(outputs, dim=1)
            confidence = probabilities[0][predicted_idx].item() * 100
            prediction = class_names[predicted_idx.item()]

        # === 关键修改 #1：使用相对路径 ===
        # 旧的错误代码: img_url = f'http://127.0.0.1:5000/static/uploads/{filename}'
        # 新的正确代码:
        img_url = f'/static/uploads/{filename}'
        
        return jsonify({
            'prediction': prediction, 
            'confidence': f'{confidence:.2f}%', 
            'img_url': img_url
        })

@app.route('/api/records', methods=['GET'])
def get_records():
    records_query = Record.query.order_by(Record.timestamp.desc()).all()
    records_list = []
    for record in records_query:
        # === 关键修改 #2：确保返回的也是相对路径 ===
        # 旧的逻辑可能会拼接成一个完整的 http 地址，现在我们确保它是一个干净的相对路径
        # 假设数据库存的是 'static/uploads/image.jpg'
        img_path = record.img_url
        if not img_path.startswith('/'):
            img_path = '/' + img_path

        records_list.append({
            'id': record.id,
            'user': record.user.username,
            'img_url': img_path,
            'prediction': record.prediction,
            'confidence': record.confidence,
            'is_correct': record.is_correct,
            'timestamp': record.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
    return jsonify(records_list)

# 用于提供上传的图片
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000, debug=True)
