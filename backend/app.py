from flask import Flask, request, jsonify
from flask_cors import CORS
import requests # 专门用来发送网络请求
import os

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 定义模型服务的地址。
# 假设模型服务会运行在本地的 5001 端口
MODEL_SERVICE_URL = "http://127.0.0.1:5001/predict"

# 创建一个文件夹来临时存放上传的图片
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        # 准备要发送给模型服务的数据
        # 'files' 这个 key 必须和模型服务接收端的名字匹配
        files = {'file': (file.filename, file.read(), file.mimetype)}
        
        try:
            # 向模型服务发送 POST 请求
            response = requests.post(MODEL_SERVICE_URL, files=files)
            
            # 检查模型服务是否成功返回
            if response.status_code == 200:
                # 将模型服务的返回结果直接转发给前端
                return jsonify(response.json())
            else:
                # 如果模型服务出错，也把错误信息返回给前端
                error_msg = f"Error from model service: {response.status_code} {response.text}"
                print(error_msg)
                return jsonify({'error': error_msg}), 500

        except requests.exceptions.RequestException as e:
            # 如果连接模型服务失败（比如模型服务没启动）
            error_msg = f"Could not connect to model service: {e}"
            print(error_msg)
            return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    # 后端服务运行在默认的 5000 端口
    app.run(host='0.0.0.0', port=5000, debug=True)
