import os
import json
import time
import requests

from flask import jsonify, g, Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql import func, text
import pymysql
from HslCommunication import SiemensS7Net, SiemensPLCS
from threading import Thread

config = {
    "PLC_IP_ADR": '172.21.3.1'
}
cur_path = os.getcwd()
if os.path.exists(cur_path + '\\config.json'):
    with open(cur_path + '\\config.json', 'r') as f:
        config = json.load(f)
else:
    with open(cur_path + '\\config.json', 'w') as f:
        json.dump(config, f)
app = Flask(__name__)

CORS(app, supports_credentials=True)
pymysql.install_as_MySQLdb()
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://Festo:Festo4.0@127.0.0.1:3306/wms_db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ECHO"] = True
db = SQLAlchemy(app, session_options={"autocommit": True})
PREFIX_URL = '/api'
PLC = SiemensS7Net(SiemensPLCS.S1500, config.get('PLC_IP_ADR'))
PLC.receiveTimeOut = 1000
PLC.connectTimeOut = 1000
PLC_CONN_Tag = False


class Part_DB(db.Model):
    # 记录每个产品的数据
    __tablename__ = 'part'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tower_code = db.Column(db.CHAR(2), server_default='')
    prod_code = db.Column(db.CHAR(4), server_default='')
    time_code = db.Column(db.CHAR(8), server_default='')
    part_num = db.Column(db.Integer, server_default=text('0'))
    date = db.Column(DATETIME(fsp=2), server_default=func.now(2))


class WMS_DB(db.Model):
    # 记录已经发送给WMS的数据
    __tablename__ = 'wms'
    # 流水号
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    tray_code = db.Column(db.String(30), server_default='')
    part_num = db.Column(db.Integer, server_default=text('0'))
    date = db.Column(DATETIME(fsp=2), server_default=func.now(2))


@app.route(PREFIX_URL + '/adb')
def createDB():
    db.create_all()
    return 'CREATED DATABASE COMPLETE'


def comm():
    global PLC_CONN_Tag
    while True:
        result = PLC.ConnectServer()
        if result.IsSuccess:
            PLC_CONN_Tag = True
            while True:
                result = PLC.ReadBool('I0.0')
                if result.IsSuccess:
                    print("PLC is Running. Time is", str(time.time()))
                    time.sleep(2)
                else:
                    break
        else:
            print("PLC is Not Running. Time is", str(time.time()))
            time.sleep(2)


def cycle_():
    while True:
        print("WMS is Running. Time is", str(time.time()))
        time.sleep(2)


@app.before_first_request
def F():
    Thread(target=comm).start()
    Thread(target=cycle_).start()
    return


@app.route(PREFIX_URL + '/')
def get_version():  # put application's code here
    return 'Version: 1.0.0'


@app.route(PREFIX_URL + '/data/add')
def addProd():
    obj = Part_DB(tower_code='01')
    db.session.add(obj)
    db.session.flush()
    return 'Add Done'


url = 'http://www.baidu.com'


@app.route('/get')
def get():
    r = requests.get(url)
    r.encoding = 'utf-8'
    return r.text


@app.route('/time')
def getTime():
    sftime = time.strftime('%Y%m%d')
    # 20221101
    return sftime


# TODO 在网页上显示实时时间
# TODO 显示总加工数量
# TODO 显示异常产品的数量
# TODO 右边显示已经向WMS发送的托盘信息/已完成的托盘信息
# TODO 下方显示每个塔位当前的状态
if __name__ == '__main__':
    app.run()
