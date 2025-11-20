import redis
import json
import os
from typing import Any, Dict, List

class RedisClient:
    def __init__(self):
        self.redis_url = os.environ.get('AIRFLOW__CELERY__BROKER_URL', 'redis://:@redis:6379/0')
        self.client = redis.from_url(self.redis_url)
    
    def push_to_queue(self, queue_name: str, data: Dict[str, Any]):
        """Push data to specific Redis queue"""
        self.client.rpush(queue_name, json.dumps(data))
        print(f"✅ Données poussées dans la queue {queue_name}")
    
    def pop_from_queue(self, queue_name: str) -> Dict[str, Any]:
        """Pop data from Redis queue"""
        data = self.client.lpop(queue_name)
        if data:
            return json.loads(data)
        return None
    
    def get_queue_length(self, queue_name: str) -> int:
        """Get queue length"""
        return self.client.llen(queue_name)
    
    def publish_message(self, channel: str, message: Dict[str, Any]):
        """Publish message to Redis channel"""
        self.client.publish(channel, json.dumps(message))
    
    def get_all_queues(self) -> List[str]:
        """Get all queue names"""
        return [key.decode() for key in self.client.keys() if key.decode().startswith('queue_')]

redis_client = RedisClient()