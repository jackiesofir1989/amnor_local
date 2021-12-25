import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import utc

from task_manager import worker

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.WARNING)
scheduler = AsyncIOScheduler(timezone=utc)


def add_all_jobs():
    scheduler.add_job(worker.add_a_lamp_query_to_queue, 'interval', seconds=2, id='add_a_lamp_query_to_queue')
    scheduler.add_job(worker.add_a_lamp_group_membership, 'interval', minutes=1, id='add_a_lamp_group_membership')
    scheduler.add_job(worker.add_a_lamp_non_important_query_to_queue, 'interval', minutes=3, id='add_a_lamp_non_important_query_to_queue')
    scheduler.add_job(worker.add_a_sensor_query_to_queue, 'interval', seconds=30, minutes=0, id='add_a_sensor_query_to_queue')
    scheduler.add_job(worker.set_a_blower_to_queue, 'interval', minutes=10, id='set_a_blower_to_queue')
    scheduler.add_job(worker.set_group_settings, 'interval', minutes=10, id='set_group_settings')
    worker.set_group_settings()
    worker.add_a_sensor_query_to_queue()
