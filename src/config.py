from os import environ as env
import multiprocessing

PORT = int(env.get("PORT", 8080))

# Gunicorn config
bind = ":" + str(PORT)
workers = 1
# preload_app = True
worker_tmp_dir = "/dev/shm"

# def on_starting(server):
#      print(1)