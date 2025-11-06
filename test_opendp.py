import pandas as pd
import numpy as np
from app.utils.opendp_handler import OpenDPHandler

# 创建测试数据
test_data = pd.DataFrame({
    'age': np.random.randint(18, 80, 1000),
    'income': np.random.normal(50000, 15000, 1000),
    'education': np.random.choice(['High School', 'Bachelor', 'Master', 'PhD'], 1000),
    'city': np.random.choice(['New York', 'Los Angeles', 'Chicago', 'Houston'], 1000)
})

print("Test data created successfully")
print(test_data.head())

# 测试OpenDP处理器
try:
    opendp_handler = OpenDPHandler()
    print("OpenDP Handler initialized successfully")
    
    # 测试准备上下文
    context = opendp_handler.prepare_context(test_data, privacy_budget=1.0)
    print("Context prepared successfully")
    
    # 测试创建合成器
    synthesizer = opendp_handler.create_dp_synthesizer({'algorithm': 'AIM', 'epsilon': 1.0})
    print("Synthesizer created successfully")
    
    # 测试训练
    opendp_handler.fit(test_data, {'algorithm': 'AIM', 'epsilon': 1.0})
    print("Model trained successfully")
    
    # 测试生成数据
    synthetic_data = opendp_handler.sample(100)
    print("Synthetic data generated successfully")
    print(synthetic_data.head())
    
    print("All tests passed!")
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()