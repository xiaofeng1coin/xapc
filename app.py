from flask import Flask, render_template, request, redirect, flash
import threading
import paho.mqtt.client as mqtt
from wakeonlan import send_magic_packet
import db
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# 初始化数据库
db.init_db()

# --- 全局变量：关机信号 ---
# False = 正常, True = 准备关机
# 当收到MQTT关机指令时，设为True；Windows轮询读到True后，将其重置为False
shutdown_signal = False

# --- MQTT 逻辑 ---
def on_connect(client, userdata, flags, rc):
    print(f"MQTT Connected with result code {rc}")
    cfg = db.get_config()
    if cfg and cfg['bemfa_topic']:
        client.subscribe(cfg['bemfa_topic'])

def on_message(client, userdata, msg):
    global shutdown_signal
    msg_str = msg.payload.decode('utf-8')
    print(f"收到MQTT指令: {msg.topic} -> {msg_str}")
    
    if msg_str == "on":
        # 开机逻辑 (WOL)
        cfg = db.get_config()
        if cfg and cfg['pc_mac']:
            print(f"执行WOL唤醒: {cfg['pc_mac']}")
            send_magic_packet(cfg['pc_mac'])
            
    elif msg_str == "off":
        # 关机逻辑：设置信号位
        print("收到关机指令，等待Windows轮询...")
        shutdown_signal = True

def mqtt_loop():
    while True:
        cfg = db.get_config()
        # 只有配置了才连接
        if cfg and cfg['bemfa_uid'] and cfg['bemfa_topic']:
            client = mqtt.Client()
            client.on_connect = on_connect
            client.on_message = on_message
            try:
                # 巴法云地址
                client.connect("bemfa.com", 9501, 60)
                client.loop_forever()
            except Exception as e:
                print(f"MQTT连接异常: {e}, 5秒后重试")
                time.sleep(5)
        else:
            time.sleep(10)

# 启动MQTT后台线程
threading.Thread(target=mqtt_loop, daemon=True).start()

# --- Flask 路由 ---

@app.route('/', methods=['GET', 'POST'])
def index():
    cfg = db.get_config()
    if request.method == 'POST':
        db.update_config(
            request.form['uid'],
            request.form['topic'],
            request.form['mac']
        )
        flash('配置已保存，请等待MQTT重连生效', 'success')
        return redirect('/')
    return render_template('index.html', config=cfg)

# --- Windows 轮询接口 ---
@app.route('/check_shutdown')
def check_shutdown():
    global shutdown_signal
    if shutdown_signal:
        shutdown_signal = False  # 读完一次就复位
        return "YES"
    else:
        return "NO"

# --- 手动API接口 ---
@app.route('/api/on')
def api_on():
    cfg = db.get_config()
    if cfg and cfg['pc_mac']:
        send_magic_packet(cfg['pc_mac'])
        return "WOL Sent"
    return "MAC not configured"

@app.route('/api/off')
def api_off():
    global shutdown_signal
    shutdown_signal = True
    return "Shutdown Signal Set"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
