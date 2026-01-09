from utils.logging_helper import set_logger
from utils.settings_loader import load_settings
from services.git_service import GitService
from queue import Queue, Empty
import subprocess
import sys
import os
import signal
import time
import platform
import paho.mqtt.client as mqtt
import json
import threading
import psutil

SETTINGS_PATH = 'settings_local.yaml'
RUN_CODE = 'main.py'

class MqttService:
    broker: str
    port: int
    topic: str
    status_topic: str
    output_topic: str
    control_topic: str
    api_key: str


    need_time_command : list[str] = ["start_main", "stop_main", "git_update", "checkUpdated"]
    logger = set_logger('MQTT')


    def __init__(self, setting_path = SETTINGS_PATH):
        self.settings = load_settings(setting_path)
        
        self.mqtt = self.settings.get('mqtt', {})
        self.broker = self.mqtt.get('broker', '')
        self.port = self.mqtt.get('port', '')
        self.topic = self.mqtt.get('topic', '')
        self.status_topic = self.mqtt.get('status_topic', '')
        self.output_topic = self.mqtt.get('output_topic', '')
        self.control_topic = self.mqtt.get('control_topic', '')
        self.is_running = False
        self.client = None
        self.process: subprocess.Popen = None
        self.Bulid_client()
        self.current_app = {'name': 'main', 'code': RUN_CODE}


        self.init_command_queue()
        self.start_command_worker()



    def _get_mqtt_params(self):
        api_key = self.settings.get('api_key')

        if not api_key:
            self.logger.error('API Key is not set')

        for key, value in self.mqtt.items():
            if isinstance(value, str) and 'api_key_' in value:
                value = value.replace('api_key_', f'{api_key}')
            setattr(self, key, value)

        self.logger.info(f'Broker: {self.broker}')
        self.logger.info(f'Port: {self.port}')
        self.logger.info(f'Topic: {self.topic}')
        self.logger.info(f'Status Topic: {self.status_topic}')
        self.logger.info(f'Output Topic: {self.output_topic}')
        self.logger.info(f'Control Topic: {self.control_topic}')

    def Bulid_client(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            self.logger.info(f'Connected to MQTT broker')
        except Exception as e:
            self.logger.error(f'Failed to connect to MQTT broker: {e}')

    def on_connect(self, client, userdata, flags, rc):
        self._get_mqtt_params()
        self.logger.info(f'Connected to MQTT broker')
        client.subscribe(self.control_topic)

    def on_message(self, client, userdata, msg):
    
        command_dict = json.loads(msg.payload.decode())
        command = command_dict.get("command")
        self.logger.info(f"Received command: {command}")
        
        # Check queue size before adding
        if self.command_queue.qsize() >= 10:  # Leave some buffer
            self.logger.warning(f"Command queue is nearly full, rejecting command: {command}")
            self._send_status(f"error:Command queue full - try again later")
            return
        
        # Queue the command for processing by the worker thread
        client_info = {"client": client, "userdata": userdata}
        try:
            self.command_queue.put((command_dict, client_info), timeout=1.0)
            self.logger.debug(f"Command '{command}' queued for processing (queue size: {self.command_queue.qsize()})")
        except:
            self.logger.error(f"Failed to queue command '{command}' - queue timeout")
            self.send_status(f"error:Failed to queue command - system busy")

    def init_command_queue(self):
        self.command_lock = threading.Lock()
        self.command_queue = Queue(maxsize = 50)
        self.command_worker_thread = None
        self.is_busy = False
        self.shutdown_event = threading.Event()
        self.max_command_timeout = 300

    def start_command_worker(self):
        self.command_worker_thread = threading.Thread(target = self.command_worker, daemon = True)
        self.command_worker_thread.start()
        self.logger.info("Command worker thread started")

    def command_worker(self):
        while not self.shutdown_event.is_set():
            try:
                command_data = self.command_queue.get(timeout = 0.1)

                self.process_command(command_data)

                self.command_queue.task_done()
            
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error in command worker: {e}")
        
    def process_command(self, command_data):
        command_dict, client_info = command_data
        command = command_dict.get("command")

        if self.is_busy and command in self.need_time_command:
            self.logger.warning(f"Rejecting command '{command}' - system is busy")
            self.send_status(f"busy:Cannot process {command} - system is currently busy")
            return

        try:
            with self.command_lock:

                if command in self.need_time_command:
                    self.is_busy = True
                    self.send_status(f"busy:Processing {command}")
                
                self.logger.info(f"Processing command: {command}")

                if command == "start_main":
                    #self.start_main()未實現函數
                    pass
                elif command == "stop_main":
                    #self.stop_main()未實現函數
                    pass
                elif command in ["git_update", "checkUpdated"]:
                    git_service = GitService()
                    git_service.update()
                else:
                    self.logger.warning(f'Unknown Command: {command}')

        except Exception as e:
            self.logger.error(f"Error in process command '{command}':{e}")
            self.send_status(f"error:Failed to process {command} - {str(e)}")

        finally:
            if self.is_busy:
                self.is_busy = False
                self.send_status(f"Command '{command}' completed, system no longer busy")
            
    def send_status(self, status: str):
        status_dict = {
            "type": "status",
            "status" : status
        }
        self.client.publish(self.status_topic, json.dumps(status_dict))

    def stream_output(self):
        while self.is_running and self._process and self._process.poll() is None:
            try:
                output = self.process.stdout.readline()
                if output:
                    output = output.strip()
                    self.client.publish(self.output_topic, output)
            except Exception as e:
                self.logger.error(f"Error reading output: {e}")
                break
            time.sleep(0.1)




    def kill_process_tree(self, pid):
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            gone, alive = psutil.wait_procs(children, timeout=3)
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            try:
                parent.terminate()
                parent.wait(timeout=3)
            except psutil.NoSuchProcess:
                pass
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            print(f"Error killing process tree: {e}")

    def graceful_shutdown_unix(self):
        """Gracefully shutdown application on Unix systems (Linux/macOS)."""
        try:
            pgid = os.getpgid(self.process.pid)
            
            # Step 1: Send SIGINT (Ctrl+C equivalent) for graceful shutdown
            self.logger.info("Sending SIGINT for graceful shutdown...")
            try:
                os.killpg(pgid, signal.SIGINT)
                self.process.wait(timeout=8)  # Wait up to 8 seconds for graceful shutdown
                self.logger.info("Process terminated gracefully with SIGINT")
                return
            except subprocess.TimeoutExpired:
                self.logger.info("SIGINT timeout, trying SIGTERM...")
            
            # Step 2: Send SIGTERM if SIGINT didn't work
            try:
                os.killpg(pgid, signal.SIGTERM)
                self.process.wait(timeout=5)  # Wait up to 5 seconds for SIGTERM
                self.logger.info("Process terminated with SIGTERM")
                return
            except subprocess.TimeoutExpired:
                self.logger.info("SIGTERM timeout, force killing process...")
            
            # Step 3: Force kill if nothing else worked
            self.kill_process_tree(self.process.pid)
            
        except psutil.NoSuchProcess:
            self.logger.info("Process already terminated")
        except Exception as e:
            self.logger.error(f"Error during Unix graceful shutdown: {e}")
            # Fall back to force kill
            self._kill_process_tree(self.process.pid)


    def start_main(self, app_code=None):
        if self.is_running:
            self.logger.info("Application is already running!")
            return

        if app_code is None:
            app_code = self.current_app['code']
        try:
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,
                'universal_newlines': True,
                'bufsize': 1,
                'encoding': 'utf-8',  #Prevent encoding error from output
                'errors': 'replace'
            }
            kwargs['preexec_fn'] = os.setsid

            self.process = subprocess.Popen([sys.executable, app_code, '--settings', SETTINGS_PATH], **kwargs)
            self.is_running = True
            self.logger.info(f"Application ({app_code}) started successfully!")
            self.send_status(f"running:{self.current_app['name']}")

            self.output_thread = threading.Thread(target=self.stream_output)
            self.output_thread.daemon = True
            self.output_thread.start()

        except Exception as e:
            self.logger.error(f"Error starting application: {e}")
            self.is_running = False
            self.send_status(f"error:{str(e)}")


    def stop_main(self):
        if not self.is_running or not self.process:
            self.logger.info("Application is not running!")
            return

        try:

            self.graceful_shutdown_unix()

            self.logger.info("Application stopped successfully!")
            self.send_status("stopped")
        except Exception as e:
            self.logger.error(f"Error stopping application: {e}")
            self.send_status(f"error:{str(e)}")
        finally:
            self.is_running = False
            self.process = None
            if self.output_thread:
                self.output_thread.join(timeout=1)


    def cleanup(self):
        
        self.logger.info("Performing cleanup...")
        
        # Signal shutdown to command worker thread
        self.shutdown_event.set()
        
        # Wait for pending commands to complete (with timeout)
        try:
            # Wait for the queue to be empty (but not indefinitely)
            timeout_start = time.time()
            while not self.command_queue.empty() and (time.time() - timeout_start) < 5.0:
                time.sleep(0.1)
            
            # Wait for worker thread to finish
            if self.command_worker_thread and self.command_worker_thread.is_alive():
                self.command_worker_thread.join(timeout=3.0)
                if self.command_worker_thread.is_alive():
                    self.logger.warning("Command worker thread did not shutdown gracefully")
        except Exception as e:
            self.logger.error(f"Error during command worker cleanup: {e}")
        
        if self.is_running:
            self.stop_main()
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception as e:
                self.logger.error(f"Error during MQTT cleanup: {e}")
        self.logger.info("Cleanup complete")









def main():

    mqtt = MqttService()


    def signal_handler(signum, frame):
        print("\nReceived termination signal. Cleaning up...")
        mqtt.cleanup()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Cleaning up...")
        mqtt.cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        mqtt.cleanup()
        sys.exit(1)
    finally:
        mqtt.cleanup()

if __name__ == '__main__':
    main()