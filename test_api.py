import requests
import time

# 测试基础URL
BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    print("测试API端点...")
    
    # 测试根路径
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"根路径测试: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"根路径测试失败: {e}")
    
    # 测试数据相关API
    try:
        response = requests.get(f"{BASE_URL}/api/data/list")
        print(f"数据列表API测试: {response.status_code}")
        if response.status_code == 200:
            print(f"  返回数据: {response.json()}")
    except Exception as e:
        print(f"数据列表API测试失败: {e}")
    
    # 测试模型相关API
    try:
        response = requests.get(f"{BASE_URL}/api/model/available")
        print(f"可用模型API测试: {response.status_code}")
        if response.status_code == 200:
            print(f"  返回数据: {response.json()}")
    except Exception as e:
        print(f"可用模型API测试失败: {e}")
    
    # 测试当前模型API
    try:
        response = requests.get(f"{BASE_URL}/api/model/current")
        print(f"当前模型API测试: {response.status_code}")
        if response.status_code == 200:
            print(f"  返回数据: {response.json()}")
    except Exception as e:
        print(f"当前模型API测试失败: {e}")
    
    # 测试合成任务API
    try:
        response = requests.get(f"{BASE_URL}/api/synthesis/tasks")
        print(f"合成任务列表API测试: {response.status_code}")
        if response.status_code == 200:
            print(f"  返回数据: {response.json()}")
    except Exception as e:
        print(f"合成任务列表API测试失败: {e}")

if __name__ == "__main__":
    test_api_endpoints()