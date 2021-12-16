from netrika_bot import *
from apscheduler.schedulers.background import BlockingScheduler

scheduler = BlockingScheduler()

scheduler.add_job(tasks, 'interval', hours=3, args=(app, ))

scheduler.start()
