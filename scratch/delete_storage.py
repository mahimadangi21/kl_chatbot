import shutil
import os
import time

path = "storage"
if os.path.exists(path):
    for i in range(5):
        try:
            shutil.rmtree(path)
            print(f"Successfully deleted {path}")
            break
        except Exception as e:
            print(f"Attempt {i+1} failed: {e}")
            time.sleep(1)
else:
    print(f"{path} does not exist")
