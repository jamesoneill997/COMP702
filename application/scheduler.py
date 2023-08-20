# Package Scheduler.
from apscheduler.schedulers.blocking import BlockingScheduler
from application import app

def initialize_app():
    print("Initializing app...")
    predictions = app.App()
    print("App initialized.")
    predictions.set_predictions()
    print("Predictions set.")
    predictions.set_results()
    print("Results set.")
    return

num_hours = 12
interval_seconds = 90#60*60*num_hours
# Create an instance of scheduler and add function.
scheduler = BlockingScheduler()
scheduler.add_job(initialize_app, "interval", seconds=interval_seconds, misfire_grace_time=None)
scheduler.start()
