import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

#config
cred = credentials.Certificate('oddsgenie-firebase.json')
app = firebase_admin.initialize_app(cred)
db = firestore.client()

load_dotenv()

class DB():
    def populate_courses(self):
        courses_endpoint = os.environ["RACING_API_URL"] + "/courses"
        params = {}
        response = requests.request(
            "GET", 
            courses_endpoint, 
            auth=HTTPBasicAuth(
                os.environ["RACING_API_USERNAME"],
                os.environ["RACING_API_PASSWORD"]), 
            params=params,
        )
        courses = response.json()["courses"]
        print(f'Refreshing {len(courses)} courses...')

        for course in courses:
            print("Adding course: " + course["course"])
            try:
                doc_ref = db.collection("courses").document(course["id"])
                doc_ref.set(
                    {
                        "course": course["course"],
                        "region_code": course["region_code"],
                        "region": course["region"],
                    }
                )
            except Exception as e:
                print(f'Error adding course: {course}')            
                print(f'Error: {e}')            

    def populate_horse(self, horse_data):
        try:
            doc_ref = db.collection("horses").document(horse_data["horse_id"])
            doc_ref.set(horse_data)
        except Exception as e:
            print(f'Error adding horse: {horse_data}')            
            print(f'Error: {e}')
            return 1
        return 0
    def check_horse(self, horse_id):
        doc_ref = db.collection("horses").document(horse_id)

        doc = doc_ref.get()
        if doc.exists:
            print(f"Document data: {doc.to_dict()}")
            return doc.to_dict()
        else:
            print(f'Horse not found: {horse_id}')
            return False

def main():
    test_horse = {
        "horse_id": "test_floats",
        "horse_name": "red rum",
        "sex": "F",
        "sire": "moyganny lass",
        "dosage": {
            "di": 1.5,
            "cd": 1.3,
            },
    }
    db = DB()
    db.check_horse("james")
    db.check_horse("test_me")
    db.populate_horse(test_horse)
    db.check_horse("test_this_out")
if __name__ == "__main__":
    main()