import time
import paho.mqtt.client as mqtt
import threading



def main():
  # 設定MQTT
    broker = "broker.emqx.io"
    port = 1883
    topic = "/test"
    #設定一個事件
    connect = threading.Event()
    # 連接成功 rc會是0
    def on_connect(client, userdata, flags, rc) :
        #這裡判斷有沒有成功
        if rc == 0:
            client.subscribe(topic)
            print("\033[32m Connected\033[0m to MQTT broker")
            #設定事件
            connect.set()
        else:
            print("\033[31m Failed\033[0m Connect to MQTT broker")
    # 收到消息
    def on_message(client, userdata, msg):
        # 打印收到消息(主題, 內容)
        print(f"Received message: {msg.topic} {msg.payload.decode()}")
    # 斷開連結
    def on_disconnect(client, userdata, rc) :
        print(f"Disconnected from MQTT broker, rc: {rc}")

    # 創建客戶端
    client = mqtt.Client()
    # 設定連結
    client.on_connect = on_connect
    # 設定收到消息
    client.on_message = on_message
    # 設定斷開連結
    client.on_disconnect = on_disconnect
    # 連結到broker
    client.connect(broker, port, 60)
    # 開始循環 主程式只要設定一次 不要重複設定到
    client.loop_start()

    # 等待連接到成功, 如果超過時間就停止
    if not connect.wait(timeout = 10):
        client.loop_stop()
        return
    # 發送消息指定(客戶端, 主題)
    mqtt_pub(client, topic)

    time.sleep(0.5)
    client.disconnect()
    client.loop_stop()



def mqtt_pub(client, topic):
    n = 0
    msg = "Hello MQTT"
    while (n < 10):
        time.sleep(1)
        info = f"Time: {time.time()}, {msg} : {n}"
        # 發送消息指定到(主題, 內容)
        result = client.publish(topic, info, qos = 1)
        # result.wait_for_publish()
        rc = result[0]
        if rc == 0:
            print("Message published\033[32m successfully\033[0m")
        else:
            print(f"\033[31m Failed\033[0m publish message, rc: {rc}")
        n += 1
if __name__ == '__main__':
    main()

"""
    mqtt 流程是:
    1.建立一個客戶端
    2.設定連接(on_connect)
    3.設定收到消息(on_message)
    4.設定斷開消息(on_disconnect)
    5.連接到broker
    6.開始循環
"""
'''
 command 工作流程是:
 1.我先init Queue 大小設為50
 2.然後鎖住我的線程 建立一個關機事件
 3.然後start command worker thread
 4.當我沒有收到關機事件的話 我就試著跑 從queue裡面get資料
 5.然後跑process command(從queue裡面get到的資料) 然後檢視完成 task_done
 6.with lock的方式來排程 一次處理一個command
 7.判斷是不是我定義的長指令 如果是就進入busy 狀態將這狀態傳送給mqtt
 8.將收到command的指令資料來對應我定義的function執行
 9.並記算完成時間
 10.完成後將busy狀態設為false 並傳送給mqtt
'''