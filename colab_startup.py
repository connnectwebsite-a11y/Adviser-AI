# Adviser AI — Colab Recovery
# Run after mounting Google Drive.

import os
import shutil
import subprocess
import sys

SOURCE = "/content/drive/MyDrive/AdviserAI/source"
RUNTIME = "/content/adviser"

if not os.path.isdir(SOURCE):
    raise RuntimeError(
        "Adviser AI source was not found in Google Drive."
    )

# Recreate disposable runtime copy.
if os.path.exists(RUNTIME):
    shutil.rmtree(RUNTIME)

shutil.copytree(
    SOURCE,
    RUNTIME
)

print("✅ Adviser AI source restored")

# Install dependencies.
subprocess.check_call([
    sys.executable,
    "-m",
    "pip",
    "install",
    "-q",
    "-r",
    os.path.join(
        RUNTIME,
        "requirements.txt"
    )
])

print("✅ Dependencies installed")
print("✅ Runtime: /content/adviser")
print()
print("Next: load GROQAPIKEY from Colab Secrets.")
