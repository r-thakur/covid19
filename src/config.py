from os import environ as env
import multiprocessing

PORT = int(env.get("PORT", 8080))

# Gunicorn config
bind = ":" + str(PORT)
workers = multiprocessing.cpu_count() * 2 + 1
# preload_app = True
worker_tmp_dir = "/dev/shm"
timeout = 120

# def on_starting(server):
#      print(1)