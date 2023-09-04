from fixtures import RaceCard
from model import NeuralNet
from datetime import datetime
import torch
import os
import pandas as pd
from io import StringIO
from dataset_generator.firebase.config import DB
from dataset_generator.racingapi import data

class App():
    def __init__(self):
        script_directory = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.abspath(os.path.join(script_directory, '../model/bin/reduced_dataset_model_v2')) #todo fetch from remote
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.rc_manager = RaceCard(self.today)
        self.model = self.load_model()
        self.racecards = self.rc_manager.format_racecards()
        self.race_ids = self.racecards[0]
        self.racecards_raw = self.racecards[1]
        self.db = DB()
        
    def load_model(self):
        model = NeuralNet.NeuralNet()
        model.load_state_dict(torch.load(self.model_path, map_location=torch.device('cpu') ))
        model.eval()
        return model
        
    def get_racecards(self, results_limit=None, horse_limit=6):
        return self.rc_manager.format_racecards(results_limit, horse_limit)
    
    def set_predictions(self):
        print("Setting predictions...")
        predictions = {}
        racecards = self.racecards[1]
        csv_racecard_entries = [self.rc_manager.dict_to_ordered_csv(racecards[i]) for i in range(len(racecards))]
        print(f'Found {len(csv_racecard_entries)} racecards to process.')
        for csv_racecard in enumerate(csv_racecard_entries):
            data = StringIO(csv_racecard[1])
            df = pd.read_csv(data)
            tensor = torch.tensor(df.values, dtype=torch.float32)
            prediction_values = self.model(tensor).tolist()[0]
            print("Prediction values: ", prediction_values)
            predictions[self.race_ids[csv_racecard[0]]] = {f'horse_{i}':prediction_values[i] for i in range(len(prediction_values))}            

        for prediction in predictions:
            predictions[prediction]["winner_index"] = int(max(predictions[prediction], key=predictions[prediction].get)[-1])
            self.db.create_prediction_entry(prediction, predictions[prediction])

        return predictions
    
    def set_results(self):
        results = data.Results()
        results_list = results.get_results(num_days = 2)
        results.process_results(results_list)
        return True
def main():
    app = App()
    app.set_predictions()

if __name__ == "__main__":
    main()