import firebase_admin
from firebase_admin import credentials, firestore
import json
import sys
import os
import pandas as pd
from copy import deepcopy

"""
    This file is used to export the firebase data to a json file, and to convert between json and csv.
    Instructions for use:
        To export data from firebase to a json file:
            python3 exports.py export <collection1,collection2,...> <path_filename>
        To convert a json file to csv:
            python3 exports.py convert <path_filename>
"""

class Export():
    def __init__(self, init=False):
        #config
        self.script_directory = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(self.script_directory, 'oddsgenie-firebase.json')
        self.cred = credentials.Certificate('./dataset_generator/firebase/oddsgenie-firebase.json')
        if init:
            self.app = firebase_admin.initialize_app(self.cred)
            self.db = firestore.client()
    def cross_join(self, left, right):
        new_rows = [] if right else left
        for left_row in left:
            for right_row in right:
                temp_row = deepcopy(left_row)
                for key, value in right_row.items():
                    temp_row[key] = value
                new_rows.append(deepcopy(temp_row))
        return new_rows

    def flatten_list(self, data):
        for elem in data:
            if isinstance(elem, list):
                yield from self.flatten_list(elem)
            else:
                yield elem

    def json_to_dataframe(self, data_in):
        def flatten_json(data, prev_heading=''):
            if isinstance(data, dict):
                rows = [{}]
                for key, value in data.items():
                    rows = self.cross_join(rows, flatten_json(value, prev_heading + '.' + key))
            elif isinstance(data, list):
                rows = []
                for item in data:
                    [rows.append(elem) for elem in self.flatten_list(flatten_json(item, prev_heading))]
            else:
                rows = [{prev_heading[1:]: data}]
            return rows

        return pd.DataFrame(flatten_json(data_in))

    def export(self, collection_names, path_filename):
        collections = dict()
        dict4json = dict()
        n_documents = 0

        for collection in collection_names:
            print(f'Exporting {collection} to {path_filename}')
            collections[collection] = self.db.collection(collection).get()
            dict4json[collection] = {}
            print(f"Found {len(collections[collection])} documents in {collection}")
            for document in collections[collection]:
                docdict = document.to_dict()
                dict4json[collection][document.id] = docdict
                n_documents += 1

        jsonfromdict = json.dumps(dict4json)

        print("Downloaded %d collections, %d documents and now writing %d json characters to %s" % ( len(collection_names), n_documents, len(jsonfromdict), path_filename ))
        with open(path_filename, 'w') as the_file:
            the_file.write(jsonfromdict)
        print("Done.")

    #convert json file to csv format, more suitable for training data
    def json_to_csv(self, path_filename):
        with open(path_filename, encoding='utf-8') as inputfile:
            df = pd.read_json(inputfile)

        df.to_csv(f'{path_filename[:path_filename.index(".")]}.csv', encoding='utf-8', index=False)

def main():
    # export(['dataset'], './export.json')
    with open('./reduced_export.json', encoding='utf-8') as inputfile:
        df = pd.read_json(inputfile)
    
        pd.json_normalize(df["dataset"], meta=['header']).to_csv('./reduced_export.csv', encoding='utf-8', index=False)

    # command = sys.argv[1]
    # if command == 'export':
    #     collection_names = sys.argv[2].split(',')
    #     path_filename = sys.argv[3]
    #     export(collection_names, path_filename)
        
    # elif command == 'convert':
    #     path_filename = sys.argv[2]
    #     json_to_csv(path_filename)
        
        
    
if __name__ == "__main__":
    main()