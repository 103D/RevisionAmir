import sys
sys.path.insert(0, "app")
from service import RevisionService
from redis_store import RedisStore

service = RevisionService(RedisStore())
result = service.list_filials()
import json
print(json.dumps(result[0], indent=2, ensure_ascii=False))
