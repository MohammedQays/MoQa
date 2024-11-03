import time
import subprocess

# تشغيل سكربت البوت الأساسي
print("تشغيل البوت من سكربت runner.py")
subprocess.Popen(["python", "bot.py"])

# الاستمرار في العمل لمدة ساعة (3600 ثانية)
time.sleep(3600)  # التوقف بعد ساعة

print("تم إيقاف البوت بعد مرور ساعة.")
