#custom imports
from dataset_generator.pedigree.data import HorsePedigree
from dataset_generator.firebase.config import DB
from dataset_generator.firebase.exports import Export

#3rd party imports
import requests
import os
import locale
import regex as re
import urllib.parse
import pandas as pd
import csv

from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import datetime, timedelta
from io import StringIO

load_dotenv()
db = DB()
class RaceCard():
    ID_TYPE_TOKENS = {
        "hrs": 1,
        "jck": 2,
        "own": 3,
        "crs": 4,
        '':-1,
        
    }
    
    GOING_TOKENS = {
        "standard": 1,
        "slow": 2,
        "fast": 3,
        "standard to slow": 4,
        "standard to fast": 5,
        "hard": 6,
        "firm": 7,
        "good to firm": 8,
        "good": 9,
        "good to soft": 10,
        "soft": 11,
        "heavy": 12,
        "good to yielding": 13,
        "yielding": 14,
        "yielding to soft": 15,
        "very soft": 16,
        "sloppy": 17,
        "wet fast": 18,
        "muddy": 19,
        "sealed": 20,
        '':-1,
        
    }
    
    SURFACE_TOKENS = {
        "dirt": 1,
        "turf": 2,
        "all weather": 3,
        "aw": 3,
        "synthetic": 4,
        '':-1,
    }
    COUNTRY_TOKENS = {
        "IRE": 1,
        "GB": 2,
        "USA": 3,
        "GER": 4,
        "FR": 5,
        "HK": 6,
        "AUS": 7,
        "JPN": 8,
        "SIN": 9,
        "CAN": 10,
        "NZ": 11,
        "SAF": 12,
        "BRZ": 13,
        "UAE": 14,
        "ITY": 15,
        "ARG": 16,
        "KOR": 17,
        "IND": 18,
        "SPA": 19,
        "TUR": 20,
        "CZE": 21,
        "SWE": 22,
        "NOR": 23,
        "DEN": 24,
        "POL": 25,
        "BEL": 26,
        "RUS": 27,
        "CHI": 28,
        "MAC": 29,
        "PHI": 30,
        "PER": 31,
        "URU": 32,
        "POR": 33,
        "MEX": 34,
        "MOR": 35,
        '':-1,
        
    }
    
    SEX_TOKENS = {
        "F": 1,
        "C": 2,
        "G": 3,
        "H": 4,
        "M": 5,
        "R": 6,
        '':-1,
        
    }
    
    HEADGEAR_TOKENS = {
        "h": 1,
        "b": 2,
        "p": 3,
        "ht": 4,
        "tp": 5,
        "v": 6,
        "t": 7,
        "tb": 8,
        "tv": 9,
        "hb": 10,
        "htp": 11,
        "hp": 12,
        "het": 13,
        "eb": 14,
        "htb": 15,
        "e/s": 16,
        "et": 17,
        "he": 18,
        '':-1,
    }
    
    GRADE_TOKENS = {
        "grade 1": 1,
        "grade 2": 2,
        "grade 3": 3,
        "group 1": 4,
        "group 2": 5,
        "group 3": 6,
        "listed": 7,
        '':-1,
    }
    
    FORM_TOKENS = {
        "PU": 100,
        "F": 101,
        "UR": 102,
        "NR": 103,
        "R": 104,
        "BD": 105,
        "CO": 106,
        "RO": 107,
        "SU": 108,
        "RR": 109,
        "DSQ": 110,
        "-": 111,
        "/": 112,
        "V": 113,
        "": -1,
    }

    def __init__(self, date):
        self.id = None
        self.endpoint = os.getenv("RACING_API_URL") + "/racecards/pro"
        
    def get_racecards(self):
        url = "api.theracingapi.com/v1/racecards/pro"
        todays_date = datetime.today().strftime('%Y-%m-%d')
        merged_results = []
        for date in range(3):
            day = (datetime.today() - timedelta(days=date)).strftime('%Y-%m-%d') if date == 0 else (datetime.today() + timedelta(days=date)).strftime('%Y-%m-%d')
            params = {
                'date': day,
            }
            response = requests.request(
                "GET", 
                self.endpoint, 
                auth=HTTPBasicAuth(
                    os.getenv('RACING_API_USERNAME'),
                    os.getenv('RACING_API_PASSWORD')), 
                params=params,
            )
            merged_results += response.json()["racecards"]
        return merged_results
    
    #extract relevant data to comply with reduced dataset
    def format_racecards(self, result_limit=6, runner_limit=6):
        raw_cards = self.get_racecards()
        race_ids = []
        cards = []
        for i in range(len(raw_cards)):
            card = raw_cards[i]
            if len(card["runners"]) > runner_limit:
                continue
            race_id = card['race_id']
            race_ids.append(race_id)
            db.create_prediction_entry(race_id, card)
            formatted_card = {
                "distance": self.convert_distance_to_yards(card["distance"]),
                "going": self.GOING_TOKENS[card["going"].lower()],
                "is_flat": int(card["type"] == "Flat"),
                "prize_money": self.parse_prize_money(card["prize"]),
                "race_rating": self.parse_class(card["race_class"]),
                "surface": self.SURFACE_TOKENS[card["surface"].lower()],
                "tot_runners": len(card["runners"]),
            }
            
            for j in range(len(card["runners"])):
                runner = card["runners"][j]
                stored_data = db.check_horse(runner["horse_id"], self.strip_id_prefix(runner["horse_id"])) #id, name, sex, sire, dosage
                horse_has_dosage = db.horse_has_dosage(runner["horse_id"], self.strip_id_prefix(runner["horse_id"]))
                try:
                    dosage = stored_data["dosage"] if horse_has_dosage and stored_data else HorsePedigree(runner["horse"], runner["sire"]).dosage[0],
                except (KeyError, IndexError):
                    dosage = [{
                        "di": None,
                        "cd": None,
                    }]
                print(f'Horse {j} - {runner["horse"]} - {runner["horse_id"]} - {runner["sire"]}')
                formatted_card[f'horse_{j}'] = {
                    "age": int(runner["age"]),
                    "dosage.di": float(dosage[0]["di"]) if dosage[0]["di"] else 0,
                    "dosage.cd": float(dosage[0]["cd"]) if dosage[0]["cd"] else 0,
                    "draw": int(runner["draw"]) if "draw" in runner and runner["draw"] not in ['', None] else -1,
                }
                form = self.parse_form(runner["form"]) #list up to length 4, the form limit
                for k in range(len(form)):
                    formatted_card[f'horse_{j}_form_{k}'] = self.FORM_TOKENS[form[k]] if form[k] in self.FORM_TOKENS else form[k]

            cards.append(formatted_card)
        return race_ids, cards
    def parse_form(self, s):
        s = s.replace(' ', '').replace('F', '101').replace('P', '100').replace('U', '102').replace('R', '104').replace('B', '105').replace('C', '106').replace('O', '107').replace('S', '108').replace('D', '109').replace('Q', '110').replace('-', '-1')
        return list(s[-4:]) if len(s) >= 4 else list(s)
    def strip_id_prefix(self, doc_id):
        prefix, _, rest = doc_id.partition('_')
        if prefix in self.ID_TYPE_TOKENS:
            return f"{self.ID_TYPE_TOKENS[prefix]}{rest}"
        else:
            return rest

    def parse_class(self, s):
        try:
            numeric_part = re.search(r'\d+', s).group()
            return int(numeric_part)
        except AttributeError:
            return -1
    #takes mfy and returns y
    def convert_distance_to_yards(self, s):
        miles = re.search(r'(\d+)m', s)
        furlongs = re.search(r'(\d+)f', s)
        yards = re.search(r'(\d+)y', s)
        
        miles = int(miles.group(1)) if miles else 0
        furlongs = int(furlongs.group(1)) if furlongs else 0
        yards = int(yards.group(1)) if yards else 0
        
        total_yards = (miles * 1760) + (furlongs * 220) + yards
        return total_yards
    
    def parse_prize_money(self, s):
        numeric_part = re.search(r'[\d,]+', s).group().replace(',', '')
        return int(numeric_part)
    
    #super messy, but it works
    #TODO: refactor once dataset has improved
    def dict_to_ordered_csv(self, dict):
        complete_cols = [
            'distance',	'going','is_flat','prize_money',	'race_rating',	'surface',	'horse_0_form_0',	'horse_0_form_1',	'horse_0_form_2',	'horse_0_form_3',	'horse_1_form_0',	'horse_1_form_1',	
            'horse_1_form_2',	'horse_1_form_3',	'horse_2_form_0',	'horse_2_form_1',	'horse_2_form_2',	'horse_2_form_3',	'horse_3_form_0',	'horse_3_form_1',	'horse_3_form_2',	'horse_3_form_3',	
            'horse_0.age',	'horse_0.dosage.cd',	'horse_0.dosage.di',	'horse_0.draw',	'horse_1.age',	'horse_1.dosage.cd',	'horse_1.dosage.di',	'horse_1.draw',	'horse_2.age',	'horse_2.dosage.cd',	
            'horse_2.dosage.di',	'horse_2.draw',	'horse_3.age',	'horse_3.dosage.cd',	'horse_3.dosage.di',	'horse_3.draw',	'horse_4_form_0',	'horse_4_form_1',	'horse_4_form_2',	
            'horse_4_form_3',	'horse_4.age',	'horse_4.dosage.cd',	'horse_4.dosage.di',	'horse_4.draw',	'horse_5_form_0',	'horse_5_form_1',	'horse_5_form_2',	'horse_5_form_3',	'horse_5.age',	
            'horse_5.dosage.cd',	'horse_5.dosage.di',	'horse_5.draw',
        ]
        blank_df = pd.DataFrame(columns=complete_cols)
        df = Export().json_to_dataframe(dict)
        actual_cols = df.columns.to_list()
        actual_size = len(actual_cols)
        missing_cols = list(set(complete_cols) - set(actual_cols))
        for i in range(len(missing_cols)):
            df.insert(i+actual_size, missing_cols[i], 0)
        csv = df.to_csv(encoding='utf-8', index=False)
        df = pd.read_csv(StringIO(csv)).fillna(0)

        #setting headings as they appear in the dataset that the model was trained on
        #TODO standardise headings by sorting alphabetically
        df = df [complete_cols]
        csv = df.to_csv(encoding='utf-8', index=False)
        return csv

# def main():
#     today = datetime.today().strftime('%Y-%m-%d')
#     rc = RaceCard(today)
#     todays_racecards = rc.format_racecards()
#     rc.dict_to_ordered_csv(todays_racecards[0])

# if __name__ == "__main__":
#     main()