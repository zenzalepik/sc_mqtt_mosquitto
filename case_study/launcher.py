# file: case_study/launcher.py
import subprocess
import os

# root folder project
ROOT = r"D:\Github\sc_mqtt_mosquitto"

# daftar aplikasi yang mau dijalankan
apps = {
    "smart_light": os.path.join(ROOT, "case_study", "smart_light.py"),
    "monitor": os.path.join(ROOT, "case_study", "smart_light2", "monitor.py"),
    "remote": os.path.join(ROOT, "case_study", "smart_light2", "remote.py"),
}

processes = []

for name, path in apps.items():
    log_file = os.path.join(ROOT, "case_study", f"{name}.log")
    print(f"[launcher] Menjalankan {name} -> {path}")
    with open(log_file, "w") as f:
        # jalankan tiap aplikasi, arahkan output ke file log
        p = subprocess.Popen(["python", path], stdout=f, stderr=f)
        processes.append((name, p, log_file))

# tunggu semua proses selesai
for name, p, log_file in processes:
    p.wait()
    print(f"[launcher] Proses {name} selesai. Log tersimpan di {log_file}")
