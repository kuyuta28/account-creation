"""Start registrar with proper Python path."""
import os
import sys
from pathlib import Path

# Add paths: registrar root dir (for 'src' package), then common/src
root = "D:/business/account-creation/registrar"
sys.path.insert(0, root)
sys.path.insert(0, "D:/business/account-creation/common/src")
os.chdir(root)

import uvicorn
uvicorn.run("src.api.server:app", host="0.0.0.0", port=8709, reload=False)