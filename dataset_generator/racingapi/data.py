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

import pprint

load_dotenv()

class Race():
    def __init__(self):
        self.id = None
class Horse():
    def __init__(self):
        self.id = None
class RaceCard():
    def __init__(self):
        self.id = None
class Results():
    def __init__(self):
        self.id = None
        self.endpoint = os.getenv("RACING_API_URL") + "/results"
    def get_results(self, limit=50, skip=0, num_days=365):
        db = db
        data = {
            'race': {},
            'horse': {},
        }
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
        for result in results_list:
            #race data
            data['race']['id'] = result["race_id"]
            data['race']['date'] = result["date"]
            data['race']['going'] = result["going"]
            data['race']['racecourse_id'] = result["course_id"]
            data['race']['country'] = result["region"]
            data['race']['is_flat']= result["type"] == "Flat"
            data['race']['distance'] = result["dist_y"]
            data['race']['local_time'] = result["off"]
            data['race']['race_rating'] = result["pattern"]
            data['race']['winner'] = result["runners"][0]
            
            #race data that needs to be formatted or calculated
            data['race']['prize_money'] = self.format_prize_money(result["runners"][0]["prize"])
            data['race']['race_index'] = self.get_race_index(data['race']['date'], data['race']['racecourse_id'], data['race']['local_time'])
            data['race']['local_weather'] = self.get_weather(result["course"], data['race']['date'], data['race']['local_time'])
            data['race']['competitors'] = self.get_competitors(result["runners"])
            data['race']['draw'] = self.get_draw(result["runners"])
            data['race']['surface'] = self.get_surface(result)
            data['horse'] = self.get_horse_data(result["runners"])
        
        db.populate_dataset_entry(data)
        return data
            
    def get_competitors(self, runners):
        return [runner["horse_id"] for runner in runners]
    
    def get_surface(self, race):
        dirt_going = ["fast", "wet fast", "good", "muddy", "sloppy", "slow", "sealed"] # for dirt tracks, these are the going descriptions, see https://en.wikipedia.org/wiki/Going_(horse_racing))
        country = race["region"]
        return "dirt" if race["going"] in dirt_going and country == "USA" else "turf"

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
    
    def get_horse_data(self, runners):
        data = {}
        #horse data
        for runner in runners:
            stored_data = db.check_horse(runner["horse_id"]) #id, name, sex, sire, dosage
            data[runners.index(runner)] = {}
            data[runners.index(runner)]['name'], data[runners.index(runner)]['nationality'], data[runners.index(runner)]['sire'] = self.parse_horse_name_details(runner)
            data[runners.index(runner)]['sex'] = runner["sex"]
            data[runners.index(runner)]['age'] = runner["age"]
            data[runners.index(runner)]['headgear'] = runner["headgear"]
            data[runners.index(runner)]['dosage'] = stored_data["dosage"] if stored_data else self.get_dosage(runner["horse"], data[runners.index(runner)]['sire'])
            data[runners.index(runner)]['weight'] = runner["weight_lbs"]
            data[runners.index(runner)]['form'] = self.get_form(runner["horse_id"])
            data[runners.index(runner)]['weight_change'] = self.calculate_weight_change(data[runners.index(runner)]['weight'], data[runners.index(runner)]['form'][0]["weight"])
            data[runners.index(runner)]['jockey'] = runner["jockey_id"]
            data[runners.index(runner)]['trainer'] = runner["trainer_id"]
            data[runners.index(runner)]['owner'] = runner["owner_id"]
            data[runners.index(runner)]['odds'] = runner["sp_dec"]
            data[runners.index(runner)]['rating'] = runner["or"] #official rating
            if not stored_data:
                horse_data = {
                    "horse_id": runner["horse_id"],
                    "name": data[runners.index(runner)]['name'],
                    "sex": runner["sex"],
                    "sire": data[runners.index(runner)]['sire'],
                    "dosage": data[runners.index(runner)]['dosage'],
                }
                db.populate_horse(horse_data)
            
        return data
    
    #Will be an object, not an array of numbers as commonly seen in the industry
    #This allows for some context around how they performed, relative to the race
    #eg. They could have come down/gone up in class, or had a significant weight change
    def get_form(self, horse, max_history=6):
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
            result_ctx = {}
            pos = self.get_position(horse, results_list[i])
            
            #race data
            result_ctx["race_id"] = results_list[i]["race_id"]
            result_ctx["date"] = results_list[i]["date"]
            result_ctx["course"] = results_list[i]["course"]
            result_ctx["time_start"] = results_list[i]["off"]
            result_ctx["race_type"] = results_list[i]["type"]
            result_ctx["race_class"] = results_list[i]["class"]
            result_ctx["race_distance"] = results_list[i]["dist_y"]
            result_ctx["going"] = results_list[i]["going"]
            
            #horse data
            result_ctx["finishing_position"] = pos["position"]
            result_ctx["starting_price"] = results_list[i]["runners"][pos["index"]]["sp_dec"]
            result_ctx["weight"] = results_list[i]["runners"][pos["index"]]["weight_lbs"]
            result_ctx["jockey"] = results_list[i]["runners"][pos["index"]]["jockey_id"]
            result_ctx["performance_comment"] = results_list[i]["runners"][pos["index"]]["comment"] #thought this might be interesting to add
            
            form.append(result_ctx)     
            
        return form
    
    def get_position(self, horse_id, result):
        for runner in result["runners"]:
            if runner["horse_id"] == horse_id:
                return {
                    "position": runner["position"],
                    "index": result["runners"].index(runner)
                    }
        
    def calculate_weight_change(self, previous_weight, current_weight):
        return float(current_weight) - float(previous_weight)
    
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
            if result["off"] == time:
                return i
            i+=1
            
        return 0
    
    def get_dosage(self, horse_name, sire_name):
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
        
def main():
    results = Results()
    limit = 4 #number of races per request
    for i in range(2): #runmer of requests
        results.get_results(limit=limit, skip=limit*i)

    # results.get_results()
if __name__ == "__main__":
    main()