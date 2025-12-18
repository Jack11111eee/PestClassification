# test_pro.py
import requests
import time
import os

# 配置
BASE_URL = "http://localhost:5002"
TEST_TASK_ID = "test_task_" + str(int(time.time()))
# !!! 请修改这里为你服务器上真实存在的、有图片的文件夹 !!!
TEST_FOLDER = "/home/hzcu/repo/demo/model/test_images" 

def test_pipeline():
    print(f"--- 1. 检查服务健康 ---")
    try:
        resp = requests.get(f"{BASE_URL}/health")
        print(f"Health: {resp.json()}")
    except Exception as e:
        print(f"❌ 服务没启动？{e}")
        return

    print(f"\n--- 2. 发起批量任务 (Folder: {TEST_FOLDER}) ---")
    if not os.path.exists(TEST_FOLDER):
        print(f"❌ 测试文件夹不存在: {TEST_FOLDER}，请修改脚本中的 TEST_FOLDER")
        return

    payload = {"task_id": TEST_TASK_ID, "folder_path": TEST_FOLDER}
    resp = requests.post(f"{BASE_URL}/batch/start", json=payload)
    print(f"Start Response: {resp.json()}")

    print(f"\n--- 3. 模拟前端轮询进度 ---")
    while True:
        resp = requests.get(f"{BASE_URL}/batch/status/{TEST_TASK_ID}")
        data = resp.json()
        
        status = data.get('status')
        progress = data.get('progress')
        metrics = data.get('metrics', {})
        
        print(f"Status: {status} | Progress: {progress}% | Processed: {metrics.get('processed')}/{metrics.get('total')}")
        
        if status == 'completed':
            print("\n✅ 任务完成！结果预览（前3条）:")
            # 打印前 3 个结果看看对不对
            results = data.get('results', [])
            for res in results[:3]:
                print(res)
            break
        elif status == 'failed':
            print(f"\n❌ 任务失败: {data}")
            break
        
        time.sleep(1) # 模拟每秒轮询一次

if __name__ == "__main__":
    test_pipeline()
