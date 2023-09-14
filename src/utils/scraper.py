import requests
from bs4 import BeautifulSoup
from pprint import pprint
import re
import json
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
            ##class "obtain-approach-table" for obtain approach info
            ##class "obtain-limited" to check if limited op
            class "tag-cell" for tag info
            ##var myStats from last script in first article for base and per-level stats
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


def parse_stat_obj(script):
    op_stat_str = re.findall('var myStats = ({.+})\s+var summon_stats',
                             script.text.replace("\n", ""))[0]
    op_stat_object = json.loads(op_stat_str)

    del op_stat_object["ne"]["arts"]
    op_stat_object["ne"]["block"] = op_stat_object["ne"]["Base"]["block"]
    del op_stat_object["ne"]["Base"]["block"]
    del op_stat_object["ne"]["Max"]["block"]

    op_stat_object["e0"] = op_stat_object["ne"]
    del op_stat_object["ne"]

    if op_stat_object["e1"]["cost"] == "":
        del op_stat_object["e1"]
    else:
        del op_stat_object["e1"]["arts"]
        op_stat_object["e1"]["block"] = op_stat_object["e1"]["Base"]["block"]
        del op_stat_object["e1"]["Base"]["block"]
        del op_stat_object["e1"]["Max"]["block"]

    if op_stat_object["e2"]["cost"] == "":
        del op_stat_object["e2"]
    else:
        del op_stat_object["e2"]["arts"]
        op_stat_object["e2"]["block"] = op_stat_object["e2"]["Base"]["block"]
        del op_stat_object["e2"]["Base"]["block"]
        del op_stat_object["e2"]["Max"]["block"]

    return op_stat_object


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

    # Gampress URL Name
    operator_info["gamepress_url_name"] = name

    # Gamepress URL
    operator_info["gamepress_link"] = url

    # Operator Rarity
    operator_info["rarity"] = len(
        soup.find("div", class_="rarity-cell").findAll("img"))

    # Operator Description
    op_desc = soup.findAll("div", class_="description-box")
    operator_info["description"] = op_desc[1].text.strip()

    # Operator Quote
    operator_info["quote"] = op_desc[2].text.strip()

    # Alter Name
    alter = soup.find("a", class_="alter-form")
    if alter:
        operator_info["alter"] = alter.find("div", class_="name").text
    else:
        operator_info["alter"] = None

    # Operator Secondary Stats
    op_2nd_stats = soup.findAll("div", class_="other-stat-value-cell")
    for stat in op_2nd_stats:
        name = stat.find(class_="effect-title").text.strip()
        stat_2nd_lookup = {
            "Arts Resist": "resist",
            "Redeploy Time": "redeploy",
            "DP Cost": "cost",
            "Block": "block",
            "Attack Interval": "interval"
        }
        operator_info[stat_2nd_lookup[name]] = stat.find(
            class_="effect-description").text.strip()

    # Operator Level Stats
    op_stat_script_article = soup.find("article", class_="operator-node")
    op_stat_script = op_stat_script_article.findAll("script")[-1]
    op_stat_object = parse_stat_obj(op_stat_script)
    operator_info["level_stats"] = op_stat_object

    # Operator Potentials
    op_pots = soup.find("div", class_="potential-cell")
    operator_info["potentials"] = parse_pots(op_pots)

    # Operator Trust Bonuses
    op_trust = soup.find("div", class_="trust-cell")
    operator_info["trust_stats"] = parse_trust(op_trust)

    # Limited
    op_obtain_info = soup.find(class_="obtain-approach-table").text.strip()
    limited = re.search("LIMITED", op_obtain_info)

    operator_info["limited"] = True if limited else False

    # EN Release Info
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
    cn_release = re.search(
        "Release Date \(CN\)\n(\d+/\d+/\d\d\d\d)",
        op_obtain_info
    )
    cn_recruit = re.search(
        "Recruitment Pool Date \(CN\)\n(\d+/\d+/\d\d\d\d)",
        op_obtain_info
    )

    operator_info["CN_released"] = True if cn_release else False
    operator_info["CN_release_date"] = mdy2ymd(
        cn_release.group(1)) if cn_release else None
    operator_info["CN_recruitable"] = True if cn_recruit else False
    operator_info["CN_recruitment_added"] = mdy2ymd(
        cn_recruit.group(1)) if cn_recruit else None

    # Archetype Class Name
    op_class = soup.findAll("div", class_="profession-title")
    archetype_info["class_name"] = op_class[0].text.strip()

    # Archetype Name
    archetype_info["archetype_name"] = op_class[1].text.strip()

    # Archetype Trait
    trait_info = op_desc[0]
    for s in trait_info.select("pre"):
        s.extract()
    archetype_info["trait"] = trait_info.text.strip()

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

    # Archetype Cost Gains On Promotion
    e1_cost_gain = None
    e2_cost_gain = None
    if operator_info["rarity"] > 2:
        e1_cost_gain = op_stat_object["e1"]["cost"] > op_stat_object["e0"]["cost"]
        if operator_info["rarity"] > 3:
            e2_cost_gain = op_stat_object["e2"]["cost"] > op_stat_object["e1"]["cost"]
    archetype_info["cost_gain_on_E1"] = e1_cost_gain
    archetype_info["cost_gain_on_E2"] = e2_cost_gain

    # Archetype Block Gains On Promotion
    e1_block_gain = None
    e2_block_gain = None
    if operator_info["rarity"] > 2:
        e1_block_gain = op_stat_object["e1"]["block"] > op_stat_object["e0"]["block"]
        if operator_info["rarity"] > 3:
            e2_block_gain = op_stat_object["e2"]["block"] > op_stat_object["e1"]["block"]
    archetype_info["block_gain_on_E1"] = e1_block_gain
    archetype_info["block_gain_on_E2"] = e2_block_gain

    del op_stat_object["e0"]["cost"], op_stat_object["e0"]["block"]
    if operator_info["rarity"] > 2:
        del op_stat_object["e1"]["cost"], op_stat_object["e1"]["block"]
        if operator_info["rarity"] > 3:
            del op_stat_object["e2"]["cost"], op_stat_object["e2"]["block"]

    return operator_info, archetype_info


if __name__ == "__main__":
    pprint(scrape("horn"))
