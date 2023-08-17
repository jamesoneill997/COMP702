#custom imports
from pedigree.data import HorsePedigree
from firebase.config import DB

#3rd party imports
import requests
import os
import locale
import regex as re
import urllib.parse

from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from datetime import datetime, timedelta
from meteostat import Hourly, Stations
from multiprocessing import Pool

import pprint

load_dotenv()
db = DB()

class Results():
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
        "": -1,
    }

    def __init__(self):
        self.id = None
        self.endpoint = os.getenv("RACING_API_URL") + "/results"
    def get_results(self, limit=50, skip=0, num_days=365):
        params = {
            "limit": limit,
            "skip": skip,
        }
        if not num_days == 365:
            d = datetime.today() - timedelta(days=num_days)
            params["start_date"] = d.strftime('%Y-%m-%d')
            params["end_data"] = datetime.today().strftime('%Y-%m-%d')
        response = requests.request(
            "GET", 
            self.endpoint, 
            auth=HTTPBasicAuth(
                os.getenv('RACING_API_USERNAME'),
                os.getenv('RACING_API_PASSWORD')), 
            params=params,
        )

        results_list = response.json()["results"]
        return results_list

    def process_results(self, results_list):
        print(f'Processing {len(results_list)} entries...')
        for result in results_list:
            try:
                if not self.validate_label(result):
                    print("No valid label found for this race - skipping")
                    continue
                if db.check_dataset_entry(result["race_id"]): #skip races we've already processed
                    print(f"Skipping race {result['race_id']} - entry already exists")
                    continue
                print(f"Parsing result {results_list.index(result) + 1} of {len(results_list)} results")
                data = {}
                surface = self.get_surface(result)
                draw = self.get_draw(result["runners"])
                #race data
                data['id'] = int(self.strip_id_prefix(result["race_id"]))
                data['date'] = self.unix_time(result["date"])
                data['going'] = self.GOING_TOKENS[result["going"].lower()] if self.GOING_TOKENS[result["going"].lower()] else -1
                data['racecourse_id'] = int(self.strip_id_prefix(result["course_id"]))
                data['country'] = self.COUNTRY_TOKENS[result["region"]] if self.COUNTRY_TOKENS[result["region"]] else -1
                data['is_flat']= int(result["type"] == "Flat")
                data['distance'] = int(result["dist_y"]) 
                data['local_time'] = int(self.convert_to_military_time(result["off"]))
                data['race_rating'] = self.GRADE_TOKENS[result["pattern"].lower()] if self.GRADE_TOKENS[result["pattern"].lower()] else -1
                data['winner'] = int(result["runners"][0]["draw"] )#this is the label, super important!
                
                #race data that needs to be formatted or calculated
                data['prize_money'] = self.format_prize_money(result["runners"][0]["prize"])
                data['race_index'] = self.get_race_index(result['date'], result['course_id'], result['off'])
                data['local_weather'] = self.get_weather(result["course"], result['date'], result['off'])
                data['draw'] = {}
                for i in range(len(draw)):
                    data['draw'][str(i)] = int(draw[i])
                data['surface'] = self.SURFACE_TOKENS[surface] if self.SURFACE_TOKENS[surface] else -1
                for runner in result["runners"]:
                    data[f'horse_{result["runners"].index(runner)}'] = self.get_horse_data(runner)
            
                db.populate_dataset_entry(data, result["race_id"])
            except Exception as e:
                print(f"Error processing result {results_list.index(result) + 1} of {len(results_list)} results")
                print(e)
                continue
        return
            
    def get_competitors(self, runners):
        return [runner["horse_id"] for runner in runners]
    
    def get_surface(self, race):
        dirt_going = ["fast", "wet fast", "good", "muddy", "sloppy", "slow", "sealed"] # for dirt tracks, these are the going descriptions, see https://en.wikipedia.org/wiki/Going_(horse_racing)
        country = race["region"]
        return "dirt" if race["going"].lower() in dirt_going and country == "USA" else "turf"

    def format_prize_money(self, prize_money):
        trimmer = re.compile(r'[^\d.,]+')
        trimmed = trimmer.sub('', prize_money)

        decimal_separator = trimmed[-3:][0]
        if decimal_separator not in [".", ","]:
            decimal_separator = None

        trimmer = re.compile(rf'[^\d{decimal_separator}]+')
        trimmed = trimmer.sub('', prize_money)

        if decimal_separator == ",":
            trimmed = trimmed.replace(",", ".")

        result = float(trimmed)
        return result

    def get_draw(self, runners):
        return [runner["draw"] for runner in runners]
    
    def validate_label(self, data):
        return data["runners"][0]["draw"] not in [None, ""]

    def format_date_time(self, date, time):
        date_time = {}
        date_split = date.split("-")
        time_split = time.split(":")
        date_time["year"] = int(date_split[0])
        date_time["month"] = int(date_split[1])
        date_time["day"] = int(date_split[2])
        date_time["hour"] = int(time_split[0])
        date_time["minute"] = int(time_split[1])
        
        return date_time
    
    def get_weather(self, racecourse_name, date, time):
        time_period = self.format_date_time(date, time)     
        try:
            # Set time period
            start = datetime(time_period["year"], time_period["month"], time_period["day"], time_period["hour"])
            end = datetime(time_period["year"], time_period["month"], time_period["day"], time_period["hour"], time_period["minute"])
            course_coords = self.get_location(racecourse_name)     
                
            stations = Stations()
            stations = stations.nearby(course_coords[0], course_coords[1])
            station = stations.fetch(1).index[0]

            data = Hourly(station, start, end)
            data = data.fetch()
        
            data_dict = data.iloc[0].to_dict()
        
        except Exception as e:
            print(e)
            data_dict = -1
        return data_dict
        
    def get_location(self, racecourse_name):
        url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(racecourse_name) +'?format=json'

        response = requests.get(url).json()
        try:
            lat = response[0]["lat"]
            lon = response[0]["lon"]
        except IndexError as e:
            print(e)
            return [0,0]
        return [float(lat), float(lon)]
    
    def get_horse_data(self, runner):
        data = {}
        #horse data
        form, previous_weight = self.get_form_and_weight(runner["horse_id"])
        stored_data = db.check_horse(runner["horse_id"], self.strip_id_prefix(runner["horse_id"])) #id, name, sex, sire, dosage
        horse_has_dosage = db.horse_has_dosage(runner["horse_id"], self.strip_id_prefix(runner["horse_id"]))
        data['id'] = int(self.strip_id_prefix(runner["horse_id"]))
        data['nationality'] = self.COUNTRY_TOKENS[self.get_nationality(runner["horse"])] if self.COUNTRY_TOKENS[self.get_nationality(runner["horse"])] else -1
        data['sex'] = self.SEX_TOKENS[runner["sex"]] if self.SEX_TOKENS[runner["sex"]] else -1
        data['age'] = int(runner["age"]) if runner["age"] else -1
        data['headgear'] = self.HEADGEAR_TOKENS[runner["headgear"]] if self.HEADGEAR_TOKENS[runner["headgear"]] else -1
        data['dosage'] = stored_data["dosage"] if horse_has_dosage and stored_data else self.get_dosage(runner["horse"], runner['sire'])
        data['weight'] = int(runner["weight_lbs"]) if runner["weight_lbs"] else -1
        for i in range(len(form)): 
            data[f'form_{i}'] = int(form[i]) if form[i] not in self.FORM_TOKENS else self.FORM_TOKENS[form[i]]
        data['weight_change'] = self.calculate_weight_change(previous_weight, data['weight'])
        data['jockey'] = int(self.strip_id_prefix(runner["jockey_id"])) 
        data['trainer'] = int(self.strip_id_prefix(runner["trainer_id"])) 
        data['owner'] = int(self.strip_id_prefix(runner["owner_id"]))
        data['odds'] = float(runner["sp_dec"]) if runner["sp_dec"] not in [None, "", "–"] else -1
        data['rating'] = int(runner["or"]) if runner["or"] not in [None, "", "–"] else -1
        data['draw'] = int(runner["draw"]) if runner["draw"] else -1
        if not stored_data or not horse_has_dosage:
            horse_data = {
                "horse_id": self.strip_id_prefix(runner["horse_id"]),
                "name": runner['horse'],
                "sex": self.SEX_TOKENS[runner["sex"]] if self.SEX_TOKENS[runner["sex"]] else -1,
                "sire": runner['sire'],
                "dosage": data['dosage'],
            }
            db.populate_horse(horse_data)
        
        return data
    
    #Will be an object, not an array of numbers as commonly seen in the industry
    #This allows for some context around how they performed, relative to the race
    #eg. They could have come down/gone up in class, or had a significant weight change
    def get_form_and_weight(self, horse, max_history=6):
        form = []
        horse_results_endpoint = os.environ["RACING_API_URL"] + f'/horses/{horse}/results'
        params = {
            "limit": max_history,
        }
        response = requests.request(
            "GET", 
            horse_results_endpoint, 
            auth=HTTPBasicAuth(
                os.getenv('RACING_API_USERNAME'),
                os.getenv('RACING_API_PASSWORD'), 
            ), 
            params=params
        )
        results_list = response.json()["results"]
        for i in range(min(max_history, len(results_list))):
            # result_ctx = {}
            pos = self.get_position(horse, results_list[i])
            
            #race data
            # result_ctx["race_id"] = self.strip_id_prefix(results_list[i]["race_id"])
            # result_ctx["date"] = self.unix_time(results_list[i]["date"])
            # result_ctx["course"] = self.strip_id_prefix(results_list[i]["course"])
            # result_ctx["time_start"] = self.convert_to_military_time(results_list[i]["off"])
            # result_ctx["race_type"] = results_list[i]["type"] #tokenize
            # result_ctx["race_class"] = self.strip_id_prefix(results_list[i]["class"])
            # result_ctx["race_distance"] = results_list[i]["dist_y"]
            # result_ctx["going"] = self.GOING_TOKENS[results_list[i]["going"]] if self.GOING_TOKENS[results_list[i]["going"]] else -1 #tokenize
            
            #horse data
            # result_ctx["finishing_position"] = pos["position"]
            # result_ctx["starting_price"] = results_list[i]["runners"][pos["index"]]["sp_dec"]
            # result_ctx["weight"] = results_list[i]["runners"][pos["index"]]["weight_lbs"]
            # result_ctx["jockey"] = self.strip_id_prefix(results_list[i]["runners"][pos["index"]]["jockey_id"])
            
            form.append(pos)
        try:
            last_weight = results_list[0]["runners"][pos["index"]]["weight_lbs"]
        except Exception as e:
            last_weight = -1
        
        return form, last_weight
    
    def get_position(self, horse_id, result):
        for runner in result["runners"]:
            if runner["horse_id"] == horse_id:
                return  runner["position"] # "index": result["runners"].index(runner)
    
    def calculate_weight_change(self, previous_weight, current_weight):
        return 0 if previous_weight == -1 else float(current_weight) - float(previous_weight)
    
    def get_race_index(self, date, course_id, time):
        params = {
            'start_date': date,
            'end_date': date,
            'course': course_id,
        }
        response = requests.request(
            "GET", self.endpoint, 
            auth=HTTPBasicAuth(
                os.getenv('RACING_API_USERNAME'),
                os.getenv('RACING_API_PASSWORD'),    
            ),
            params=params
            )
        results = response.json()
        i = 1
        
        for result in results["results"]:
            if self.convert_to_military_time(result["off"]) == self.convert_to_military_time(time):
                return i
            i+=1
            
        return 0
    
    def get_dosage(self, horse_name, sire_name):
        horse_name = horse_name[:horse_name.index('(')].strip() if '(' in horse_name else horse_name
        sire_name = sire_name[:sire_name.index('(')].strip() if '(' in sire_name else sire_name
        pedigree = HorsePedigree(horse_name, sire_name)
        dosage = pedigree.dosage
        
        return dosage
    
    
    def parse_horse_name_details(self, runner):
        match = re.match(r'^(.*?) \((.*?)\)$', runner["horse"])
        horse_name, nationality, sire = (None, None, None)
        if match:
            horse_name, nationality = match.groups()
        sire = runner["sire"]

        return(horse_name.strip(), nationality.strip(), sire.strip())
    
    def strip_id_prefix(self, doc_id):
        prefix, _, rest = doc_id.partition('_')
        if prefix in self.ID_TYPE_TOKENS:
            return f"{self.ID_TYPE_TOKENS[prefix]}{rest}"
        else:
            return rest
        
    def unix_time(self, time):
        epoch = datetime.strptime(time, "%Y-%m-%d").timestamp()
        return epoch
    
    def convert_to_military_time(self, time):
        return time.replace(":", "")
    
    def get_race_info(self, race_id):
        race_pro_endpoint = os.environ["RACING_API_URL"] + f'/racecards/{race_id}/pro'

        params = {}
        response = requests.request(
            "GET", 
            race_pro_endpoint, 
            auth=HTTPBasicAuth(
                os.getenv('RACING_API_USERNAME'),
                os.getenv('RACING_API_PASSWORD')), 
            params=params,
        )
        
        print(response.json())
        
    def get_nationality(self, horse_name):
        pattern = r'\((\w+)\)$'  # Matches text inside parentheses at the end of the string
        match = re.search(pattern, horse_name)
        if match:
            return match.group(1)
        else:
            return None

def main():
    results = Results()
    # results.get_race_info("rac_10988926")
    limit = 10 #number of races per request
    i = 0
    j = 1
    k = 2
    l = 3
    while True: 
        res_a = results.get_results(limit=limit, skip=limit*i) #this will error out when it reaches the end of the results, works fine, but maybe can be handled better
        res_b = results.get_results(limit=limit, skip=limit*j) #this will error out when it reaches the end of the results, works fine, but maybe can be handled better
        res_c = results.get_results(limit=limit, skip=limit*k) #this will error out when it reaches the end of the results, works fine, but maybe can be handled better
        res_d = results.get_results(limit=limit, skip=limit*l) #this will error out when it reaches the end of the results, works fine, but maybe can be handled better
        pool = Pool(os.cpu_count())
        pool.map(results.process_results, [res_a, res_b, res_c, res_d])
        i+=4
        j+=4
        k+=4
        l+=4

    # results.get_results()
if __name__ == "__main__":
    main()
