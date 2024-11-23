import logging
import json
from datetime import datetime
from pathlib import Path
from src.config import LOGS_DIR

class APILogger:
    def __init__(self, name: str):
        self.log_dir = LOGS_DIR / name
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建日志文件名（使用时间戳）
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"api_call_{timestamp}.json"
        
        # 创建空的日志文件
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    def _serialize_response(self, obj):
        """序列化响应对象"""
        if hasattr(obj, 'body'):
            return {
                "result": obj.body.get("result", ""),
                "error_code": obj.body.get("error_code"),
                "error_msg": obj.body.get("error_msg"),
                "id": obj.body.get("id"),
                "usage": obj.body.get("usage", {})
            }
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    def log_api_call(self, request_data: dict, response_data: dict, error: str = None):
        """记录API调用的请求和响应"""
        try:
            # 读取现有日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            # 创建新的日志条目
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "request": request_data,
                "response": self._serialize_response(response_data),
                "error": error
            }
            
            # 添加新的日志条目
            logs.append(log_entry)
            
            # 写回文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2, default=self._serialize_response)
        
        except Exception as e:
            print(f"记录日志时出错：{str(e)}")
            # 如果出错，尝试直接写入单个日志条目
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump([{
                    "timestamp": datetime.now().isoformat(),
                    "error": f"日志记录错误：{str(e)}",
                    "request": str(request_data),
                    "response": str(response_data)
                }], f, ensure_ascii=False, indent=2)