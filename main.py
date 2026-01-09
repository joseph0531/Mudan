from mqtt_service import MqttService
import time


def main():
    mqtt = MqttService()


    n = 0
    while (n < 100):

        mqtt.send_status("start_main")
        n += 1
        time.sleep(1)



if __name__ == '__main__':
    main()