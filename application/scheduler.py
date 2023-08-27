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

initialize_app()