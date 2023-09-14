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
            ##class "skill-section" for all skill info
            class "talent-child" for talents
            ##class "obtain-approach-table" for obtain approach info
            ##class "obtain-limited" to check if limited op
            class "tag-cell" for tag info
            ##var myStats from last script in first article for base and per-level stats
            module info
'''

stat_lookup = {
    "Deployment Cost": "DP Cost",
    "Redeployment Cooldown": "Redeploy Time",
    "Maximum HP": "HP",
    "Attack Power": "ATK",
    "Defense": "DEF",
    "Arts Resistance": "Arts Resist"
}


def parse_range(range_soup):
    tile_lookup = {"null-box": " ",
                   "empty-box": chr(9633),
                   "fill-box": chr(9632)}
    cols = range_soup.findAll("div", class_="range-cell")
    tileset = []
    for col in cols:
        tiles = col.findAll("span")
        column = "".join([tile_lookup[tile["class"][0]] for tile in tiles])
        tileset.append(column)
    return "\n".join(tileset)


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
            pot_desc[pot_stat] = int(pot.find(
                class_="potential-title").text.strip().replace("+", ""))
        output[pot_level] = pot_desc
    return output


def parse_trust(trust_soup):
    output = {}
    trust_stats = trust_soup.findAll("div", class_="potential-list")
    for stat in trust_stats:
        output[stat_lookup[stat.find("a").text.strip()]] = int(stat.find(
            class_="potential-title").text.strip().replace("+", ""))
    return output


def parse_stat_obj(script):
    op_stat_str = re.findall('var myStats = ({.+})\s+var summon_stats',
                             script.text.replace("\n", ""))[0]
    op_stat_object = json.loads(op_stat_str)
    new_stat_object = {}
    for key in op_stat_object:
        if op_stat_object[key]["cost"] != "":
            new_stat_object[key] = {}
            new_stat_object[key]["Base"] = {k: int(op_stat_object[key]["Base"][k])
                                            for k in ["ATK", "DEF", "HP"]}
            new_stat_object[key]["Max"] = {k: int(op_stat_object[key]["Max"][k])
                                           for k in ["ATK", "DEF", "HP", "Level"]}
            new_stat_object[key]["cost"] = int(op_stat_object[key]["cost"])
            new_stat_object[key]["block"] = int(
                op_stat_object[key]["Base"]["block"])

    new_stat_object["e0"] = new_stat_object["ne"]
    del new_stat_object["ne"]

    return new_stat_object


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
    skill_info = []
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
        if name == "Attack Interval":
            operator_info[stat_2nd_lookup[name]] = float(stat.find(
                class_="effect-description").text.strip())
        else:
            operator_info[stat_2nd_lookup[name]] = int(stat.find(
                class_="effect-description").text.strip())

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
    operator_info["archetype_name"] = archetype_info["archetype_name"]

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
    archetype_info["ranges"] = {}
    archetype_info["ranges"]["e0"] = parse_range(
        soup.find("div", {"id": "image-tab-1"}).find(
            "div", class_="range-box"
        )
    )
    if operator_info["rarity"] > 2:
        archetype_info["ranges"]["e1"] = parse_range(
            soup.find("div", {"id": "image-tab-2"}).find(
                "div", class_="range-box"
            )
        )
    if operator_info["rarity"] > 3:
        archetype_info["ranges"]["e2"] = parse_range(
            soup.find("div", {"id": "image-tab-3"}).find(
                "div", class_="range-box"
            )
        )

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

    # Skill Info
    for cell in soup.findAll("div", class_="skill-cell"):
        skill = {}
        skill["skill_name"] = re.findall("Skill \d: (.+)", cell.text)[0]
        # if skill["skill_name"] == "Destreza":
        #     print(cell)
        skill["sp_type"] = re.findall("SP Charge Type\n\n(.+)", cell.text)[0]
        skill["activation"] = re.findall(
            "Skill Activation\n\n\n(.+)", cell.text)[0]
        sp_cost_list = [item.text for item in cell.find(
            class_="sp-cost").findAll(class_="effect-description")]
        initial_sp_list = [item.text for item in cell.find(
            class_="initial-sp").findAll(class_="effect-description")]
        skill_duration_list = [item.text.strip() for item in cell.find(
            class_="skill-duration").findAll(class_="effect-description")]
        skill_description_list = [item.text.strip() for item in cell.find(
            class_="skill-description").findAll(class_="effect-description")]
        skill_level_lookup = {
            0: "L1",
            1: "L2",
            2: "L3",
            3: "L4",
            4: "L5",
            5: "L6",
            6: "L7",
            7: "M1",
            8: "M2",
            9: "M3",
        }
        range_change = bool(cell.find(class_="skill-range-box"))
        if range_change:
            skill_range_list = [
                parse_range(item) for item in cell.findAll(class_="range-box")]
        for i in range(len(sp_cost_list)):
            skill[skill_level_lookup[i]] = {
                "sp_cost": int(sp_cost_list[i]),
                "initial_sp": int(initial_sp_list[i]),
                "skill_duration": skill_duration_list[i],
                "skill_description": skill_description_list[i]
            }
            if range_change:
                skill[skill_level_lookup[i]]["range"] = skill_range_list[i]
        skill_info.append(skill)
        if not operator_info.get("skill_1_name"):
            operator_info["skill_1_name"] = skill["skill_name"]
        elif not operator_info.get("skill_2_name"):
            operator_info["skill_2_name"] = skill["skill_name"]
        else:
            operator_info["skill_3_name"] = skill["skill_name"]
    return operator_info, archetype_info, skill_info


if __name__ == "__main__":
    pprint(scrape("horn"))
    # scrape("schwarz")
