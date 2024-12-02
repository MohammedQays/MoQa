import time
import subprocess

# تشغيل سكربت البوت الأساسي
print("تشغيل البوت من سكربت runner.py")
process = subprocess.Popen(["python", "wikipedia_stub_bot.py"])

# الاستمرار في العمل لمدة ساعتين (7200 ثانية)
time.sleep(10800)  # التوقف بعد ساعتين

# طباعة رسالة عند انتهاء الفترة
print("تم إيقاف البوت بعد مرور ساعتين.")
