import requests
from bs4 import BeautifulSoup
from src.utils.scraper import scrape
from src.utils.insert import insert
import time
from src.utils.formatting import select_query
from src.utils.connect import run

skip_list = [
    "tulip",
    "touch",
    "pith",
    "stormeye",
    "sharp",
    "reserve-operator-logistics",
    "reserve-operator-caster",
    "reserve-operator-sniper",
    "reserve-operator-melee",
]


def full_scrape(new_only=True):
    url = "https://gamepress.gg/arknights/tools/"
    url += "interactive-operator-list#tags=null##stats"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    all_in = True
    for item in soup.find_all("tr", class_="operators-row"):
        title = item.find("a", class_="operator-title-actual")
        name = title["href"].split("/")[-1]
        print(name)
        if name in skip_list:
            print("IS op, skipping")
            print("")
            continue
        if item["data-availserver"] == "na":
            if new_only:
                query = select_query(
                    "operators",
                    filters={"gamepress_url_name": name}
                )
                db_res = run(query)
            else:
                db_res == []
            if db_res == []:
                all_in = False
                time.sleep(5)
                data = scrape(name)
                insert(*data)
            else:
                print("in db")
        else:
            print("cn op, skipping")
        print("")
    if all_in:
        print("all in db already")


if __name__ == "__main__":
    full_scrape()
