import os
import requests
import random
import pprint
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin.firestore import FieldFilter

from pedigree.data import HorsePedigree
from multiprocessing import Pool

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
            print("Successfully added horse")
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
        horses_ref = db.collection("horses")

        # Create a query against the collection
        query_ref = horses_ref.where(filter=FieldFilter('dosage.cd', "==", None))
        results = query_ref.get()
        return results
    
    def retry_horse_dosage(self, horses_doc_refs):
        for horse in horses_doc_refs:
            horse = horse.to_dict()
            horse["sire"] = horse["sire"][:horse["sire"].index("(")].strip() if "(" in horse["sire"] else horse["sire"]
            horse["name"] = horse["name"][:horse["name"].index("(")].strip() if "(" in horse["name"] else horse["name"]
            
            print(f"Checking {horse['name']} with sire {horse['sire']}...")
            hp = HorsePedigree(horse["name"], horse["sire"])
            horse["dosage"] = hp.dosage
            
            print(f"Adding dosage {horse['dosage']} to horse {horse['name']}")
            self.populate_horse(horse)
            
    def dataset_dosage_blank_horses(self, index):
        datset_ref = db.collection("dataset")
        query_ref = datset_ref.where(filter=FieldFilter(f'horse_{index}.dosage.cd', "==", None))
        results = query_ref.get()
        return results
        
        
    def repopulate_missing_datset_dosage(self, dataset_doc_ref, index):
        for entry in dataset_doc_ref:
            entry_dict = entry.to_dict()
            print(f'Repopulating dataset entry {dataset_doc_ref.index(entry)} of {len(dataset_doc_ref)}...')
            print(f'Checking entry {entry.id}...')
            horse_id = str(entry_dict[f"horse_{index}"]["id"])
            stored_data = self.check_horse(horse_id, horse_id)
            if not stored_data:
                print("No stored data found for horse")
                continue
            dosage = stored_data["dosage"]
            print(f'Found dosage: {dosage}')
            entry_dict[f"horse_{index}"]["dosage"] = dosage
            self.populate_dataset_entry(entry_dict, entry.id)
            
    def get_dataset(self, limit=None):
        dataset_ref = db.collection("dataset")
        dataset = dataset_ref.get() if not limit else dataset_ref.limit_to_last(limit).get()
        return dataset

def fix_horses_collection():
    db = DB()
    horses_doc_refs = db.dosage_blank_horses()
    batch_size = 10
    cpu_count = os.cpu_count()
    i = 0
    j = i+batch_size
    k = j+batch_size
    l = k+batch_size
    
    while True:
        fix_a = horses_doc_refs[i:i+batch_size]
        fix_b = horses_doc_refs[j:j+batch_size]
        fix_c = horses_doc_refs[k:k+batch_size]
        fix_d = horses_doc_refs[l:l+batch_size]

        pool = Pool(cpu_count)
        pool.map(db.retry_horse_dosage, [fix_a, fix_b, fix_c, fix_d])
        i+=batch_size*cpu_count
        j+=batch_size*cpu_count
        k+=batch_size*cpu_count
        l+=batch_size*cpu_count
        
def rearrange_dataset_entries():
    database = DB()
    dataset = DB().get_dataset()
    for entry in dataset:
        print(f'Checking entry {dataset.index(entry)} of {len(dataset)}...')
        d = entry.to_dict()
        keys = [key for key in d if "horse_" in key]
        vals = [d[key] for key in d if "horse_" in key]
        random.shuffle(keys)
        d_shuffled = dict(zip(keys, vals))
        
        for key in d_shuffled:
            d[key] = d_shuffled[key]
        database.populate_dataset_entry(d, entry.id)
        
def convert_dosage_to_float():
    database = DB()
    dataset = database.get_dataset()
    for entry in dataset:
        print(f'Checking entry {dataset.index(entry)} of {len(dataset)}...')
        d = entry.to_dict()
        for i in range(len(d["draw"])):
            if d[f'horse_{i}']["dosage"]["cd"]:
                d[f'horse_{i}']["dosage"]["cd"] = float(d[f'horse_{i}']["dosage"]["cd"])
            if d[f'horse_{i}']["dosage"]["di"]:
                d[f'horse_{i}']["dosage"]["di"] = float(d[f'horse_{i}']["dosage"]["di"])
        database.populate_dataset_entry(d, entry.id)
def main():
    db = DB()
    convert_dosage_to_float()
if __name__ == "__main__":
    main()