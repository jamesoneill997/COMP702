# Package Scheduler.
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from app import App

def initialize_app():
    print("Initializing app...")
    predictions = App()
    print("App initialized.")
    print("Setting predictions...")
    predictions.set_predictions()
    print("Setting results...")
    predictions.set_results()
    print("Done.")

num_hours = 4
interval_seconds = 60*60*num_hours
# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(initialize_app, "interval", seconds=interval_seconds, misfire_grace_time=None, next_run_time=datetime.now(), max_instances=1)
scheduler.start()
