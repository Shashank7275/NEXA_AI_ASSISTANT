import psutil
import GPUtil
import threading
import time

class AutomationCore:
    def __init__(self):
        self.monitoring = False
    
    def get_system_status(self):
        return {
            'cpu': psutil.cpu_percent(interval=1),
            'ram': round(psutil.virtual_memory().used / 1024**3, 1),
            'disk': psutil.disk_usage('/').percent,
            'gpu': self.get_gpu_usage()
        }
    
    def get_gpu_usage(self):
        try:
            gpus = GPUtil.getGPUs()
            return gpus[0].load * 100 if gpus else 0
        except:
            return 0
    
    def start_monitoring(self, callback):
        def _monitor():
            self.monitoring = True
            while self.monitoring:
                status = self.get_system_status()
                callback(status)
                time.sleep(5)
        threading.Thread(target=_monitor, daemon=True).start()
    
    def automate_task(self, task_name):
        tasks = {
            'cleanup': self.disk_cleanup,
            'update': self.system_update
        }
        return tasks.get(task_name, lambda: "Unknown task")()
    
    def disk_cleanup(self):
        return "Disk cleanup completed"
    
    def system_update(self):
        return "System updated"

    def buy_flipkart_cod(self, query):
        try:
            from flipkart import FlipkartScraper
            scraper = FlipkartScraper()
            return scraper.open_product(query)
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    core = AutomationCore()
    print(core.get_system_status())
