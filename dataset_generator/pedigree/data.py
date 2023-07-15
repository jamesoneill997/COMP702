import requests
import re
import pandas as pd

from bs4 import BeautifulSoup
from lxml import etree


class Horse():
    def __init__(self, name):
        self.name = name
        self.dosage_url = self.get_dosage_url()
        self.dosage = self.get_dosage()
    #return False if only one horse is found
    def get_horse_list(self):
        url = 'https://www.pedigreequery.com/cgi-bin/new/check2.cgi'
        payload = {
            'query_type': 'check',
            'search_bar': 'horse',
            'wsid': '1686071089',
            'h': self.name,
            'g': '5',
            'inbred': 'Standard',
            'x2': 'n',
            'chefList': '0'
        }

        response = requests.post(url, data=payload)
        html = response.content
        soup = BeautifulSoup(html,  "html.parser")
        #check if duplicates exist
        try:
            table = soup.findAll('table', width="600")[0]
        except IndexError:
            return False
        rows = table.findAll('tr')
        
        entry_dict = {}
        headings = []
        headings_html = rows[0].findAll('th')
        for heading in headings_html:
            headings.append(heading.text.strip())
            
        content = rows[1:]
        for i in range(len(content)):
            curr_entry = entry_dict[i] = {}
            cells = content[i].findAll('td')
                    
            for j in range(len(cells)):
                curr_entry[headings[j]] = cells[j].text.strip()
                
        return entry_dict

    def get_dosage_url(self):
        horse_list = self.get_horse_list()
        if not horse_list: #single horse found
            return f'https://www.pedigreequery.com/{self.name}'
        
        #TODO - add logic to select correct horse
        # will require more than just self.name, will add this once 
        # application is integrated with theracingAPI
        return None
    
    def get_dosage(self):
        di_cd = {
            "di": None,
            "cd": None,
        }
        if not self.dosage_url:
            return di_cd
        
        response = requests.get(self.dosage_url)
        html = response.content
        soup = BeautifulSoup(html,  "html.parser")
        
        horse_data = soup.findAll('table')[4]
        
        (di, cd) = self.extract_match(str(horse_data))
        if di and cd:
            di_cd['di'] = di
            di_cd['cd'] = cd
        return di_cd

    def extract_match(self, html_string):
        print("Attempting to extract match...")
        print(html_string)
        pattern = re.compile(r"DI = (-?\d+\.\d+)\s+CD = (-?\d+\.\d+)")
        match = pattern.search(html_string)
        if match:
            di_value = float(match.group(1))
            cd_value = float(match.group(2))
            return di_value, cd_value
        else:
            return None, None