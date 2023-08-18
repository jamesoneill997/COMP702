from fixtures import RaceCard
from oddgenie.model import NeuralNet
from datetime import datetime
import torch

class App():
    def __init__(self):
        self.model = self.load_model()
        self.today = datetime.today().strftime('%Y-%m-%d')
        self.get_racecards = self.get_racecards()
        self.model_path = '../model/bin/reduced_dataset_model_v1'
        self.rc_manager = RaceCard(self.today)
        
        
    def load_model(self):
        model = NeuralNet()
        model.load_state_dict(torch.load(self.model_path))
        model.eval()
        return model
        
    def get_racecards(self, results_limit=None, horse_limit=6):
        return self.rc_manager.format_racecards(results_limit, horse_limit)
        
    def get_predictions(self):
        predictions = []
        csv_racecard_entries = [self.rc_manager.dict_to_ordered_csv(self.get_racecards()[i]) for i in range(len(self.get_racecards()))]
        print(csv_racecard_entries)

def main():
    app = App()
    app.get_predictions()

if __name__ == "__main__":
    main()