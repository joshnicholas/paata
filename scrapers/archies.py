# %%

import requests
from bs4 import BeautifulSoup as bs

from sudulunu.helpers import pp, dumper
import pandas as pd 
import os

import os 
import pathlib
pathos = pathlib.Path(__file__).parent.parent
os.chdir(pathos)

def rand_delay(minium, num):
  import random 
  import time 
  rando = minium + random.random() * num
  print(rando)
  time.sleep(rando)

# %%

skipyears = ['2024']

out_path = 'data/scrapes/archies/images'
start = 'https://www.artgallery.nsw.gov.au/prizes/archibald/'


headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
'Accept-Language': "en-GB,en-US;q=0.9,en;q=0.8",
"Referer": 'https://www.google.com',
"DNT":'1'}

r = requests.get(start, headers=headers)

records = []

# %%

soup = bs(r.text, 'html.parser')
years = soup.find_all('a', class_='card-prizesCompetitionYear-link')
years = ['https://www.artgallery.nsw.gov.au' + x['href'] for x in years]

# %%

for year in years:
    if year not in skipyears:
        print(f"\n\n Starting year: {year} \n\n")
        ar = requests.get(year, headers=headers)

        new_soup = bs(ar.text, 'html.parser')
        cards = new_soup.find_all('div', class_='artworksList-item')
        year_stem = year.split("/")[-2]

        folds = os.listdir(out_path)

        if year_stem not in folds:
            os.makedirs(f"{out_path}/{year_stem}")

        # rand_delay(40, 20)

        for card in cards:
            urlo = 'https://www.artgallery.nsw.gov.au' + card.a['href']

            old = pd.read_csv('data/scrapes/archies/images/scraped.csv')

            already_done = old['Url'].unique().tolist()
            # already_done = []

            if urlo not in already_done:
                print(f"Starting: {len(already_done) + 1} ")

                artist = card.find(class_='card-artwork-artist').text

                page = requests.get(urlo , headers=headers)
                page_soup = bs(page.text, 'html.parser')

                image = page_soup.find(class_='articleHeader-image')
                
                if image:
                    image = 'https://www.artgallery.nsw.gov.au' + image['src']
                    print(image)

                    image_stemmo = image.split('/')[-1]
                    
                    image_r = requests.get(image)

                    with open(f"{out_path}/{year_stem}/{image_stemmo}", "wb") as fp:
                        fp.write(image_r.content)

                else:
                    image = ''
                    image_stemmo = ''
                    
                    print("NADA")

                medium = page_soup.find(class_='articleHeader-medium').text

                title = page_soup.find(class_='articleHeader-subtitle').text

                record = {"Artist": artist,
                        "Title": title,
                            "Medium": medium,
                            "Year": year_stem,
                        "Url": urlo,
                        "Image": image_stemmo,
                        "Image_url": image,
                        "Image_stem": image_stemmo}
                
                records.append(record)

                new = pd.DataFrame.from_records(records)

                cat = pd.concat([old,new])
                cat.drop_duplicates(subset=['Image_url'], inplace=True)

                dumper(out_path, 'scraped', cat)

                rand_delay(60, 60)

        # pp(cat)


# %%
