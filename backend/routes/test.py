from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os
import requests

test_bp = Blueprint('test', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

AI_SERVICE_URL = os.environ.get(
    "MODEL_STAFF_PREDICT_URL",
    os.environ.get("AI_SERVICE_URL", "http://127.0.0.1:8001/predict")
)
AI_SERVICE_TIMEOUT = float(os.environ.get("AI_SERVICE_TIMEOUT", "60"))

@test_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@test_bp.route('/upload', methods=['POST'])
def upload_and_predict():
    if 'images' not in request.files:
        return jsonify({'message': '没有上传文件'}), 400

    files = request.files.getlist('images')
    results = []
    errors = []

    for file in files:
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            # 转发到 AI 服务
            try:
                with open(filepath, 'rb') as f:
                    res = requests.post(
                        AI_SERVICE_URL,
                        files={'file': (filename, f, file.mimetype or 'application/octet-stream')},
                        timeout=AI_SERVICE_TIMEOUT
                    )
                res.raise_for_status()
                res_json = res.json()
            except requests.RequestException as e:
                errors.append({'filename': filename, 'error': f'AI 服务请求失败: {e}'})
                continue
            except ValueError as e:
                errors.append({'filename': filename, 'error': f'AI 服务返回的不是 JSON: {e}'})
                continue

            prediction_data = res_json.get('prediction', {}) # 使用.get()防止prediction不存在时报错
            if not prediction_data:
                errors.append({'filename': filename, 'error': res_json.get('error', 'AI 服务未返回 prediction')})
                continue

            class_name = prediction_data.get('class_name', '未知') # 同样使用.get()
            confidence = prediction_data.get('confidence', 0.0)
            results.append({
                'image_url': f"/api/test/uploads/{filename}",
                'class_name': class_name,      # 直接把 class_name 提出来
                'confidence': confidence       # 直接把 confidence 提出来
            })

    payload = {'results': results}
    if errors:
        payload['errors'] = errors
        payload['message'] = '部分或全部图片识别失败'
        return jsonify(payload), 502

    return jsonify(payload), 200
