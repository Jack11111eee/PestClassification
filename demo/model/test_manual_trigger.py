# test_manual_trigger.py
import requests
import time
from PIL import Image

# ================= 配置 =================
BASE_URL = 'http://127.0.0.1:5001'
TEST_IMG = 'test_dummy_manual.jpg'

# 1. 准备一张测试用的红图
img = Image.new('RGB', (224, 224), color='red')
img.save(TEST_IMG)

def print_step(title):
    print(f"\n{'='*10} {title} {'='*10}")

try:
    # -------------------------------------------------
    # 第一阶段：疯狂发送反馈，直到攒满阈值
    # -------------------------------------------------
    print_step("Phase 1: 正在上传反馈图片...")
    
    threshold_reached = False
    count = 0
    
    # 我们设一个上限20次，防止死循环
    for i in range(20):
        with open(TEST_IMG, 'rb') as f:
            # 模拟上传
            resp = requests.post(
                f'{BASE_URL}/feedback',
                files={'file': f},
                data={'correct_label': 'Apple_healthy'}
            )
            data = resp.json()
            count = data.get('current_count', 0)
            threshold = data.get('threshold', 0)
            is_ready = data.get('ready_to_train', False)
            
            print(f"上传第 {i+1} 张 -> 池内总数: {count}/{threshold} | Ready标志: {is_ready}")
            
            if is_ready:
                print("✨ 收到服务器信号：已达到训练阈值！")
                threshold_reached = True
                break
    
    if not threshold_reached:
        print("❌ 未达到阈值，请检查服务器配置的 RETRAIN_THRESHOLD 是否过大。")
        exit()

    # -------------------------------------------------
    # 第二阶段：验证服务器是否“偷跑”
    # -------------------------------------------------
    print_step("Phase 2: 验证服务器是否保持静默（不应自动训练）")
    
    time.sleep(2) # 给它2秒反应时间
    resp = requests.get(f'{BASE_URL}/status')
    status = resp.json()
    
    print(f"当前服务器状态: Is Training? [{status['is_training']}]")
    
    if status['is_training'] == False:
        print("✅ 验证通过：服务器很听话，没有自动开始训练。")
    else:
        print("❌ 验证失败：服务器正在偷跑！代码逻辑可能有误。")
        exit()

    # -------------------------------------------------
    # 第三阶段：手动触发训练
    # -------------------------------------------------
    print_step("Phase 3: 模拟管理员点击“开始训练”按钮")
    
    # 调用手动触发接口
    resp = requests.post(f'{BASE_URL}/retrain')
    print(f"发送 trigger 请求... 响应: {resp.json()}")
    
    if resp.status_code == 200:
        print("✅ 触发命令发送成功！")
    else:
        print(f"❌ 触发失败: {resp.text}")
        exit()

    # -------------------------------------------------
    # 第四阶段：再次检查状态
    # -------------------------------------------------
    print_step("Phase 4: 再次检查状态")
    
    time.sleep(1)
    resp = requests.get(f'{BASE_URL}/status')
    status = resp.json()
    print(f"当前服务器状态: Is Training? [{status['is_training']}]")
    
    if status['is_training'] == True:
        print("🏆 测试极其成功！流程完美闭环！")
    else:
        print("❓ 奇怪，状态怎么还是 False (也有可能跑太快结束了，或者报错了，请看服务器日志)")

finally:
    # 清理
    # import os
    # if os.path.exists(TEST_IMG): os.remove(TEST_IMG)
    pass
