import time
import subprocess

# تشغيل سكربت البوت الأساسي
print("تشغيل البوت من سكربت runner.py")
process = subprocess.Popen(["python", "wikipedia_stub_bot.py"])

time.sleep(54000)  # التوقف بعد 15 ساعة

# طباعة رسالة عند انتهاء الفترة
print("تم إيقاف البوت بعد مرور ساعتين.")
