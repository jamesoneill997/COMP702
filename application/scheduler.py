# Package Scheduler.
from apscheduler.schedulers.blocking import BlockingScheduler
from app import App



# def initialize_app():
print("Initializing app...")
predictions = App()
print("App initialized.")
print("Setting predictions...")
predictions.set_predictions()
print("Setting results...")
predictions.set_results()

print("Done.")

# num_hours = 12
# interval_seconds = 0#60*60*num_hours
# # Create an instance of scheduler and add function.
# scheduler = BlockingScheduler()
# scheduler.add_job(initialize_app, "interval", seconds=interval_seconds, misfire_grace_time=None)
# scheduler.start()
