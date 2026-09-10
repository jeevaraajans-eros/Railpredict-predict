import subprocess
out = subprocess.getoutput("python -m pytest tests/ -v")
with open("test_log.txt", "w", encoding="utf-8") as f:
    f.write(out)
