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
def populate_courses():
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
    
def main():
    #run this script to update database entries
    populate_courses()
if __name__ == "__main__":
    main()