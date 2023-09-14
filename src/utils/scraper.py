import requests
from bs4 import BeautifulSoup
from pprint import pprint
import re
''' Pseudo code for scraper func

    Args:
        operator name (format of gamepress url)

    Process:
        go to gamepress/operator name
        scrape:
            ##id "page-title" for full operator name
            ##class "rarity-cell" for rarity
            ##class "profession-title" for class and archetype
            ##class "information-cell" for position and attack type
            ##class "alter-form" for alter operator
            ##class "range-title-cell" for each range for promotion levels
            ##class "description-box" for trait, description and quote in that order
            ##class "sub-title-type-1" for potentials and trust bonuses
            class "skill-section" for all skill info
            class "talent-child" for talents
            class "obtain-approach-table" for obtain approach info
            class "obtain-limited" to check if limited op
            class "tag-cell" for tag info
            var myStats from last script in first article for base and per-level stats
'''

stat_lookup = {
    "Deployment Cost": "DP Cost",
    "Redeployment Cooldown": "Redeploy Time",
    "Maximum HP": "HP",
    "Attack Power": "ATK",
    "Defense": "DEF",
    "Arts Resistance": "Arts Resist"
}


def parse_range(range_dict):
    output = {}
    for key in range_dict:
        tile_lookup = {"null-box": " ",
                       "empty-box": chr(9633),
                       "fill-box": chr(9632)}
        soup = range_dict[key]
        cols = soup.findAll("div", class_="range-cell")
        tileset = []
        for col in cols:
            tiles = col.findAll("span")
            column = "".join([tile_lookup[tile["class"][0]] for tile in tiles])
            tileset.append(column)
        output[key] = "\n".join(tileset)
    return output


def parse_pots(pot_soup):
    output = {}
    pots = pot_soup.findAll("div", class_="potential-list")
    for pot in pots:
        pot_level = pot.find("img")["src"].split("/")[-1][0]
        if pot.find(class_="potential-title").text.strip() == "":
            pot_desc = pot.find("a").text.strip()
        else:
            pot_desc = {}
            pot_stat = stat_lookup[pot.find("a").text.strip()]
            pot_desc[pot_stat] = pot.find(
                class_="potential-title").text.strip().replace("+", "")
        output[pot_level] = pot_desc
    return output


def parse_trust(trust_soup):
    output = {}
    trust_stats = trust_soup.findAll("div", class_="potential-list")
    for stat in trust_stats:
        output[stat_lookup[stat.find("a").text.strip()]] = stat.find(
            class_="potential-title").text.strip().replace("+", "")
    return output


def mdy2ymd(date):
    mdy = date.split("/")
    ymd = [mdy[2], mdy[0], mdy[1]]
    if len(ymd[1]) == 1:
        ymd[1] = "0" + ymd[1]
    if len(ymd[2]) == 1:
        ymd[2] = "0" + ymd[2]
    return "/".join(ymd)


def scrape(name):
    url = "https://gamepress.gg/arknights/operator/"+name
    res = requests.get(url)
    operator_info = {}
    archetype_info = {}
    soup = BeautifulSoup(res.text, 'html.parser')

    # Operator Name
    operator_info["operator_name"] = soup.find(
        "div", {"id": "page-title"}).find("h1").text

    # Operator Rarity
    operator_info["rarity"] = len(
        soup.find("div", class_="rarity-cell").findAll("img"))

    # Alter Name
    alter = soup.find("a", class_="alter-form")
    if alter:
        operator_info["alter"] = alter.find("div", class_="name").text
    else:
        operator_info["alter"] = None

    # Operator Description
    op_desc = soup.findAll("div", class_="description-box")
    operator_info["description"] = op_desc[1].text.strip()

    # Operator Quote
    operator_info["quote"] = op_desc[2].text.strip()

    # Operator Potentials
    op_pots = soup.find("div", class_="potential-cell")
    operator_info["potentials"] = parse_pots(op_pots)

    # Operator Trust Bonuses
    op_trust = soup.find("div", class_="trust-cell")
    operator_info["trust_stats"] = parse_trust(op_trust)

    # Operator Secondary Stats
    op_2_stats = soup.findAll("div", class_="other-stat-value-cell")
    for stat in op_2_stats:
        name = stat.find(class_="effect-title").text.strip()
        stat_2_lookup = {
            "Arts Resist": "resist",
            "Redeploy Time": "redeploy",
            "DP Cost": "cost",
            "Block": "block",
            "Attack Interval": "interval"
        }
        operator_info[stat_2_lookup[name]] = stat.find(
            class_="effect-description").text.strip()

    # EN Release Info
    op_obtain_info = soup.find(class_="obtain-approach-table").text.strip()

    en_release = re.search(
        "Release Date \(Global\)\n(\d+/\d+/\d\d\d\d)",
        op_obtain_info
    )
    en_recruit = re.search(
        "Recruitment Pool Date \(Global\)\n(\d+/\d+/\d\d\d\d)",
        op_obtain_info
    )

    operator_info["EN_released"] = True if en_release else False
    operator_info["EN_release_date"] = mdy2ymd(
        en_release.group(1)) if en_release else None
    operator_info["EN_recruitable"] = True if en_recruit else False
    operator_info["EN_recruitment_added"] = mdy2ymd(
        en_recruit.group(1)) if en_recruit else None

    # CN Release Info
    # cn_release = re.search(
    #     "Release Date \(CN\)\n(\d+/\d+/\d\d\d\d)",
    #     op_obtain_info
    # )
    # cn_recruit = re.search(
    #     "Recruitment Pool Date \(CN\)\n(\d+/\d+/\d\d\d\d)",
    #     op_obtain_info
    # )

    # operator_info["CN_released"] = True if cn_release else False
    # operator_info["CN_release_date"] = mdy2ymd(
    #     cn_release.group(1)) if cn_release else None
    # operator_info["CN_recruitable"] = True if cn_recruit else False
    # operator_info["CN_recruitment_added"] = mdy2ymd(
    #     cn_recruit.group(1)) if cn_recruit else None

    # Limited?
    limited = re.search("LIMITED", op_obtain_info)

    operator_info["limited"] = True if limited else False

    # Archetype Name
    op_class = soup.findAll("div", class_="profession-title")
    archetype_info["archetype_name"] = op_class[1].text.strip()

    # Archetype Class Name
    archetype_info["class_name"] = op_class[0].text.strip()

    # Archetype Position
    op_position = soup.find_all("div", class_="information-cell")
    archetype_info["position"] = op_position[0].find("a").text

    # Archetype Attack Type
    archetype_info["attack_type"] = op_position[1].find("a").text

    # Archetype Range
    class_ranges = {}
    class_ranges["e0"] = soup.find("div", {"id": "image-tab-1"}
                                   ).find("div", class_="range-box")
    if operator_info["rarity"] > 2:
        class_ranges["e1"] = soup.find("div", {"id": "image-tab-2"}
                                       ).find("div", class_="range-box")
    if operator_info["rarity"] > 3:
        class_ranges["e2"] = soup.find("div", {"id": "image-tab-3"}
                                       ).find("div", class_="range-box")
    archetype_info["ranges"] = parse_range(class_ranges)

    # Archetype Trait
    trait_info = op_desc[0]
    for s in trait_info.select("pre"):
        s.extract()
    archetype_info["trait"] = trait_info.text.strip()

    return operator_info, archetype_info


if __name__ == "__main__":
    pprint(scrape("gavial-invincible"))
