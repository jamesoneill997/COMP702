import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin.firestore import FieldFilter

from pedigree.data import HorsePedigree

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
    def check_horse(self, horse_id, horse_id_v2):
        doc_ref = db.collection("horses").document(horse_id)
    
        doc = doc_ref.get()
        if not doc.exists:
            print(f"Checking {horse_id_v2}...")
            doc_ref = db.collection("horses").document(horse_id_v2)
            doc = doc_ref.get()
        if doc.exists:
            print(f"Found horse on system: {doc.to_dict()}")
            return doc.to_dict()
        else:
            print(f'Horse not found: {horse_id} // {horse_id_v2}')
            return False
        
    def horse_has_dosage(self, horse_id):
        doc_ref = db.collection("horses").document(horse_id)
        try:
            doc = doc_ref.get()
            doc = doc.to_dict()
            if "dosage" in doc:
                print(doc)
                return doc["dosage"]["cd"] is not None
            else:
                return False
        except TypeError as e:
            print(e)
            return False
        
    def check_dataset_entry(self, race_id):
        doc_ref = db.collection("dataset").document(race_id)

        doc = doc_ref.get()
        if doc.exists:
            print(f"Dataset entry found: {race_id}")
            return doc.to_dict()
        else:
            print(f'Dataset entry not found: {race_id}')
            return False
    def populate_dataset_entry(self, data, doc_id):
        print("Attempting to add dataset entry...")
        try:
            doc_ref = db.collection("dataset").document(doc_id)
            doc_ref.set(data)
            print(f"Created dataset entry for race {doc_id}")
        except Exception as e:
            print(f'Error adding dataset entry: {doc_id}')
            print(f'Error: {e}')
            return 1
        return 0
    
    def dosage_blank_horses(self):
        # Create a reference to the cities collection
        horses_ref = db.collection("dataset")

        # Create a query against the collection
        query_ref = horses_ref.where(filter=FieldFilter('horse', "", None))
        results = query_ref.get()
        return results

def main():
    db = DB()
    print(db.dosage_blank_horses())
    # print("Starting...")
    # blanks = DB().dosage_blank_horses()
    # for blank in blanks:
    #     print(f"{blanks.index(blank)+1} of {len(blanks)}")
    #     try:
    #         horse_data = blank.to_dict()
    #         for i in range(len(horse_data["horse"])):
    #             horse_name = horse_data["horse"][i]["name"]
    #             sire = horse_data["horse"][i]["sire"][:horse_data["horse"][i]["sire"].index("(")-1]
    #             dosage = HorsePedigree(horse_name, sire).dosage
    #             print(f'Dosage for {horse_name} is {dosage}')
    #             horse_data["horse"]["dosage"] = dosage
    #             print(f"Adding dosage {dosage} to horse {horse_name}")
    #             print(horse_data)
    #             #DB().populate_horse(horse_data)
    #     except Exception as err:
    #         print(f'Error adding dosage: {horse_data}')
    #         print(f'Error: {err}')
    #         continue
        
if __name__ == "__main__":
    main()