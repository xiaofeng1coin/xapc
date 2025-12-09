import sqlite3
import os

DB_NAME = 'data/config.db' # 建议放在 data 目录以便挂载

def init_db():
    # 确保 data 目录存在
    if not os.path.exists('data'):
        os.makedirs('data')
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 创建配置表
    c.execute('''CREATE TABLE IF NOT EXISTS config 
                 (id INTEGER PRIMARY KEY, 
                  bemfa_uid TEXT, 
                  bemfa_topic TEXT, 
                  pc_mac TEXT)''')
    
    # 初始化默认数据
    c.execute('SELECT count(*) FROM config')
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO config (bemfa_uid, bemfa_topic, pc_mac) VALUES ('', '', '')")
    conn.commit()
    conn.close()

def get_config():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM config WHERE id=1")
    row = c.fetchone()
    conn.close()
    return row

def update_config(uid, topic, mac):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE config SET bemfa_uid=?, bemfa_topic=?, pc_mac=? WHERE id=1", 
              (uid, topic, mac))
    conn.commit()
    conn.close()
