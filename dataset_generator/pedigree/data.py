import requests
import re
import pandas as pd

from bs4 import BeautifulSoup
from lxml import etree


class HorsePedigree():
    def __init__(self, name, sire_name):
        self.name = name
        self.sire_name = sire_name 
        self.dosage_url = self.get_dosage_url(sire_name)
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
        headings.append('Nationality') #this is part of the name in pedigree query, it is separated here to reduce abmiguity
            
        content = rows[1:]
        for i in range(len(content)):
            curr_entry = entry_dict[i] = {}
            cells = content[i].findAll('td')
                    
            for j in range(len(cells)):
                if headings[j] == 'Horse':
                    horse, nationality = self.parse_horse_name_details(cells[j].text.strip())
                    curr_entry['horse'] = horse.lower()
                    curr_entry['nationality'] = nationality

                else:
                    curr_entry[headings[j].lower()] = cells[j].text.strip().lower()
                
        return entry_dict

    def get_dosage_url(self, sire_name):
        horse_list = self.get_horse_list()
        if not horse_list: #single horse found
            return f'https://www.pedigreequery.com/{self.name}'
        
        index = self.get_pedigree_index(horse_list, sire_name)
        return f'https://www.pedigreequery.com/{self.name}{index}'
    
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
        print("Fetching dosage index for previously unseen horse...")
        # print(html_string)
        pattern = re.compile(r"DI = (-?\d+\.\d+)\s+CD = (-?\d+\.\d+)")
        match = pattern.search(html_string)
        if match:
            di_value = float(match.group(1))
            cd_value = float(match.group(2))
            return di_value, cd_value
        else:
            print("No dosage index found")
            return None, None
        
    def parse_horse_name_details(self, horse_string):
        match = re.match(r'^(.*?)\s*(?:\((.*?)\))?$', horse_string)
        horse_name, nationality = (None, None)
        if match:
            horse_name, nationality = match.groups()
            horse_name = horse_name.strip()
            nationality = nationality.strip() if nationality else None
        
        return (horse_name, nationality)
    
    #sometimes there are multiple horses with the same name
    #this function will return the correct horse by checking the sire 
    #is the same
    def get_pedigree_index(self, entry_dict, sire_name):
        print(f'Looking for {sire_name.lower()} in {self.name} pedigree')
        for k, v in entry_dict.items():
            print(f'Comparing sire {sire_name.lower().strip().replace(" ", "")} with sire {v["sire"].lower().strip().replace(" ", "")}')
            if sire_name.lower().strip().replace(' ', '') in v['sire'].lower().strip().replace(' ', ''):
                print(f"Found {self.name} with sire {v['sire'].lower().replace(' ', '')} at index {k}")
                return '' if k == 0 else str(k+1) #index 0 on pedigree website doesn't have a index suffix
        return -1 #error        


# def main():
#     horse_name="seinesational"
#     sire="Champs Elysees"
#     pedigree = HorsePedigree(horse_name, sire)
#     print(pedigree.dosage)
# if __name__ == "__main__":
#     main()