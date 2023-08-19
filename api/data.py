import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin.firestore import FieldFilter

from dataset_generator.firebase.config import DB

class Data():
    def __init__(self):
        self.db = DB()
    
    def get_results(self):
        results = self.db.get_results_by_date()
        return results
    
    def get_racecards(self):
        racecards = self.db.get_predictions_by_date()
        return racecards