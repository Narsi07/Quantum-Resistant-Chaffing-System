import sys
import os

print(f"Python executable: {sys.executable}")
print(f"Path: {sys.path}")

try:
    import oqs
    print(f"oqs imported successfully: {oqs.__file__}")
except ImportError as e:
    print(f"Failed to import oqs: {e}")
except Exception as e:
    print(f"An error occurred during import: {e}")

# Check if _oqs dir exists
oqs_dir = r"C:\Users\NARASIMMAN\_oqs"
if os.path.exists(oqs_dir):
    print(f"Found _oqs directory at {oqs_dir}")
else:
    print(f"_oqs directory not found at {oqs_dir}")
