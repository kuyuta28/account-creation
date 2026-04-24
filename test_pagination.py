"""Test pagination directly."""
import asyncio
import sys
sys.path.insert(0, "D:/business/account-creation/common/src")
sys.path.insert(0, "D:/business/account-creation/registrar/src")

from common.schemas import ok

result = ok({
    "accounts": [{"id": 1, "email": "test@test.com"}],
    "total": 100,
    "page": 1,
    "limit": 10,
    "pages": 10
})

import json
print(json.dumps(result.model_dump(), indent=2))
