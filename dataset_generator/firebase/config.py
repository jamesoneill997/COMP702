import os
import requests
import random
import pprint
import json
import random
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import (datetime, timedelta)

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin.firestore import FieldFilter

from dataset_generator.pedigree.data import HorsePedigree
from multiprocessing import Pool

#config

script_directory = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_directory, 'oddsgenie-firebase.json')
cred = credentials.Certificate(json_path) #'/dataset_generator/firebase/oddsgenie-firebase.json'
app = firebase_admin.initialize_app(cred)
db = firestore.client()

load_dotenv()

class DB():
    def create_results_entry(self, data):
        try:
            race_id = data["race_id"]
            doc_ref = db.collection("results").document(race_id)
            doc_ref.set(data, merge=True)
            print(f"Successfully added results entry {race_id}")
            return True
        except Exception as e:
            print(f"Error adding results entry: {e}")
            return False 
    def get_prediction_entry(self, race_id):
        try:
            doc_ref = db.collection("predictions").document(race_id)
            return doc_ref.get().to_dict()
        except Exception:
            return False

    def create_prediction_entry(self, race_id, data):
        try:
            doc_ref = db.collection("predictions").document(race_id)
            doc_ref.set(data, merge=True)
            print(f"Successfully added prediction entry {race_id}")
            return True
        except Exception as e:
            print(f"Error adding prediction entry: {e}")
            return False

    def get_predictions_by_date(self, date=datetime.now().strftime("%Y-%m-%d")):
        predictions_data = []
        doc_ref = db.collection("predictions")
        query_ref = doc_ref.where(filter=FieldFilter('date', ">=", date)).order_by("date").order_by("off_time")
        predictions = query_ref.get()
        predictions_dicts = {el.id: el.to_dict() for el in predictions}
        for prediction in predictions_dicts:
            winner = None
            runner_probabilities = []
            tot_runners = len(predictions_dicts[prediction]["runners"])
            for i in range(tot_runners):
                runner_probabilities.append(predictions_dicts[prediction][f'horse_{i}'])
            winner_index = runner_probabilities.index(max(runner_probabilities))
            winner = predictions_dicts[prediction]["runners"][winner_index]
            relevant_data = {
                "date": predictions_dicts[prediction]["date"] if "date" in predictions_dicts[prediction] else "TBD",
                "time": predictions_dicts[prediction]["off_time"] if "off_time" in predictions_dicts[prediction] else "TBD",
                "course": predictions_dicts[prediction]["course"],
                "runners": tot_runners,
                "prediction": predictions_dicts[prediction]["predicted_winner"] if "predicted_winner" in predictions_dicts[prediction] else "Unavailable",
                "confidence": str(predictions_dicts[prediction][f"horse_{winner_index}"]*100//1) + '%' if f"horse_{winner_index}" in predictions_dicts[prediction] else "Unavailable",
            }
            predictions_data.append(relevant_data)
            doc_ref.document(prediction).set({"predicted_winner": winner["horse"]}, merge=True)
            db.collection("results").document(prediction).set({"predicted_winner": winner["horse"]}, merge=True)
        return predictions_data
    
    def get_results_by_date(self, date = (datetime.now()-timedelta(days=2)).strftime("%Y-%m-%d")):
        results_data = []
        doc_ref = db.collection("results")
        query_ref = doc_ref.where(filter=FieldFilter('date', ">=", date)).order_by("off")
        results = query_ref.get()
        results_dicts = {el.id: el.to_dict() for el in results}
        for result in results_dicts:
            if len(results_dicts[result]["runners"]) > 6:
                continue
            try:
                prediction_entry = self.get_prediction_entry(result)
                # winner_index = prediction_entry["winner_index"] if "winner_index" in prediction_entry else None
                predicted_winner = prediction_entry["predicted_winner"] if prediction_entry else "Unavailable"
            except Exception as e:
                print(e)
                predicted_winner = "Unavailable"
            relevant_data = {
                "date": results_dicts[result]["date"] if "date" in results_dicts[result] else "TBD",
                "time": results_dicts[result]["off"] if "off" in results_dicts[result] else "TBD",
                "course": results_dicts[result]["course"],
                "runners": len(results_dicts[result]["runners"]),
                "prediction": predicted_winner,
                "result": results_dicts[result]["runners"][0]["horse"],
            }

            results_data.append(relevant_data)
            
        return results_data    
    
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
        if doc.exists:
            doc = doc.to_dict()
            doc["horse_id"] = horse_id_v2
            try:
                doc_ref.set(doc, merge=True) #This will migrate the horse_id to the new format as the system runs
                print("Migrated horse_id to v2 format")
            except Exception as e:
                print(f'Error migrating horse_id to v2 format: {e}')
            print(f"Found horse on system: {doc['name']}")
            return doc
        
        if not doc.exists:
            print(f"Checking {horse_id_v2}...")
            doc_ref = db.collection("horses").document(horse_id_v2)
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else False
        print(f'Horse not found: {horse_id} // {horse_id_v2}')
        return False
        
    def horse_has_dosage(self, horse_id, horse_id_v2):
        doc_ref = db.collection("horses").document(horse_id)
        try:
            doc = doc_ref.get()
            if not doc.exists:
                print(f"Checking {horse_id_v2}...")
                doc_ref = db.collection("horses").document(horse_id_v2)
            doc = doc_ref.get()
            if not doc.exists:
                return False
            doc = doc.to_dict()
            if "dosage" in doc:
                return doc["dosage"]["cd"] != None
            else:
                return False
        except TypeError as e:
            print(f'Error checking dosage: {e}')
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
    
    def get_reduced_dataset(self, limit=None):
        dataset_ref = db.collection("dataset")
        dataset = dataset_ref.get() if not limit else dataset_ref.limit_to_last(limit).get()
        data = []
        for entry in dataset:
            entry_dict = entry.to_dict()
            if "horse_7" in entry_dict: #only get races with 7 horses
                continue
            tmp = {
                "distance": entry_dict["distance"],
                "draw": entry_dict["draw"],
                "going": entry_dict["going"],
                "is_flat": entry_dict["is_flat"],
                "prize_money": entry_dict["prize_money"],
                "race_rating": entry_dict["race_rating"],
                "surface": entry_dict["surface"],
                "winner": entry_dict["winner"],
            }
            
            for i in range(len(entry_dict["draw"])):
                tmp[f'horse_{i}'] = {
                    "age": entry_dict[f'horse_{i}']["age"],
                    "dosage": entry_dict[f'horse_{i}']["dosage"],
                    "draw": entry_dict[f'horse_{i}']["draw"],
                    "odds": entry_dict[f'horse_{i}']["odds"],
                    "weight": entry_dict[f'horse_{i}']["weight"],
                    "sex": entry_dict[f'horse_{i}']["sex"]
                }
                for j in range(4):
                    if f'form_{j}' in entry_dict[f'horse_{i}']:
                        tmp[f"horse_{i}_form_{j}"] = entry_dict[f'horse_{i}'][f'form_{j}']
                    else:
                        continue
            data.append(tmp)

        return data

    def fix_horses_collection(self):
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
            
    def rearrange_dataset_entries(self):
        database = DB()
        dataset = DB().get_dataset()
        for entry in dataset:
            print(f'Checking entry {dataset.index(entry)} of {len(dataset)}...')
            d = entry.to_dict()
            d["winner"] = 0 #winner is always the first horse in results runners array on first run
            random_number = random.randint(0, len(d["draw"])-1)
            tmp = d["horse_0"]
            d["horse_0"] = d[f"horse_{random_number}"]
            d[f"horse_{random_number}"] = tmp
            d["winner"] = random_number

            # keys = [key for key in d if "horse_" in key]
            # vals = [d[key] for key in d if "horse_" in key]
            # random.shuffle(keys)
            # d_shuffled = dict(zip(keys, vals))
            
            # for key in d_shuffled:
            #     d[key] = d_shuffled[key]
            database.populate_dataset_entry(d, entry.id)
            
    def convert_dosage_to_float(self):
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
    reduced_dataset = db.get_reduced_dataset()
    dataset_json = json.dumps(reduced_dataset)
    with open("reduced_export.json", "w") as f:
        f.write(dataset_json)
if __name__ == "__main__":
    main()