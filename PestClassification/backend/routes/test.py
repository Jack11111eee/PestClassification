from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import requests

test_bp = Blueprint('test', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

AI_SERVICE_URL = "http://127.0.0.1:8000/predict"

@test_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@test_bp.route('/upload', methods=['POST'])
def upload_and_predict():
    if 'images' not in request.files:
        return jsonify({'message': '没有上传文件'}), 400

    files = request.files.getlist('images')
    results = []

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # 转发到 AI 服务
            try:
                with open(filepath, 'rb') as f:
                    res = requests.post(AI_SERVICE_URL, files={'file': f})
                res_json = res.json()
            except Exception as e:
                res_json = {'error': str(e)}

            prediction_data = res_json.get('prediction', {}) # 使用.get()防止prediction不存在时报错
            class_name = prediction_data.get('class_name', '未知') # 同样使用.get()
            confidence = prediction_data.get('confidence', 0.0)
            results.append({
                'image_url': f"/api/test/uploads/{filename}",
                'class_name': class_name,      # 直接把 class_name 提出来
                'confidence': confidence       # 直接把 confidence 提出来
            })

    return jsonify({'results': results}), 200
