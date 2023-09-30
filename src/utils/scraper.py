import requests
from bs4 import BeautifulSoup
# from pprint import pprint
import re
import json

stat_lookup = {
    "Deployment Cost": "DP Cost",
    "Redeployment Cooldown": "Redeploy Time",
    "Maximum HP": "HP",
    "Attack Power": "ATK",
    "Defense": "DEF",
    "Arts Resistance": "Arts Resist",
    "Attack Speed": "ASPD"
}


def parse_range(range_soup):
    tile_lookup = {"null-box": " ",
                   "empty-box": chr(9633),
                   "fill-box": chr(9632)}
    cols = range_soup.findAll("div", class_="range-cell")
    tileset = []
    for col in cols:
        tiles = col.findAll("span")
        column = [tile_lookup[tile["class"][0]] for tile in tiles]
        tileset.append(column)
    tileset = "\n".join(["".join(list(tup)) for tup in zip(*tileset)])
    return tileset


def parse_pots(pot_soup):
    output = {}
    pots = pot_soup.findAll("div", class_="potential-list")
    for pot in pots:
        pot_level = "pot" + pot.find("img")["src"].split("/")[-1][0]
        pot_stat = pot.find("a").text.strip()
        if "Talent" in pot_stat:
            pot_desc = pot_stat
        else:
            pot_desc = {}
            pot_stat = stat_lookup[pot_stat]
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
    tags = []
    modules = []
    soup = BeautifulSoup(res.text, 'html.parser')

    # Operator Name
    operator_info["operator_name"] = soup.find(
        "div", {"id": "page-title"}).find("h1").text

    # Gampress URL Name
    operator_info["gamepress_url_name"] = name

    # Gamepress URL
    operator_info["gamepress_link"] = url

    # Operator Rarity
    rarity = len(soup.find("div", class_="rarity-cell").findAll("img"))
    operator_info["rarity"] = rarity

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
        stat_name = stat.find(class_="effect-title").text.strip()
        stat_2nd_lookup = {
            "Arts Resist": "resist",
            "Redeploy Time": "redeploy",
            "DP Cost": "cost",
            "Block": "block",
            "Attack Interval": "interval"
        }
        if stat_name == "Attack Interval":
            operator_info[stat_2nd_lookup[stat_name]] = float(stat.find(
                class_="effect-description").text.strip())
        else:
            operator_info[stat_2nd_lookup[stat_name]] = int(stat.find(
                class_="effect-description").text.strip())

    # Operator Level Stats
    op_stat_script_article = soup.find("article", class_="operator-node")
    op_stat_script = op_stat_script_article.findAll("script")[-1]
    op_stat_object = parse_stat_obj(op_stat_script)
    operator_info["level_stats"] = op_stat_object

    # Operator Range
    operator_info["ranges"] = {}
    operator_info["ranges"]["e0"] = parse_range(
        soup.find("div", {"id": "image-tab-1"}).find(
            "div", class_="range-box"
        )
    )
    if rarity > 2:
        try:
            operator_info["ranges"]["e1"] = parse_range(
                soup.find("div", {"id": "image-tab-2"}).find(
                    "div", class_="range-box"
                )
            )
        except AttributeError:
            pass
    if rarity > 3:
        operator_info["ranges"]["e2"] = parse_range(
            soup.find("div", {"id": "image-tab-3"}).find(
                "div", class_="range-box"
            )
        )

    # Operator Potentials
    op_pots = soup.find("div", class_="potential-cell")
    operator_info["potentials"] = parse_pots(op_pots)

    # Operator Trust Bonuses
    op_trust = soup.find("div", class_="trust-cell")
    operator_info["trust_stats"] = parse_trust(op_trust)

    # Operator Talents Info
    talents = {}
    for t in soup.findAll("div", class_="talent-child"):
        t_name = t.find(class_="talent-title").text.strip()
        t_L = t.find(class_="operator-level").text.strip().split()[1]
        t_E = t.find(class_="elite-level")
        if not t_E:
            t_E = "0"
        else:
            t_E = t_E.find("img")["src"].split("/")[-1][0]
        t_EL = "e"+t_E+"/l"+t_L
        t_pot = "pot"+t.find(
            class_="potential-level").find("img")["src"].split("/")[-1][0]
        t_desc = t.find(
            class_="talent-description").text.strip()
        if not talents.get(t_name):
            talents[t_name] = {t_EL: {t_pot: t_desc}}
        else:
            if not talents[t_name].get(t_EL):
                talents[t_name][t_EL] = {t_pot: t_desc}
            else:
                talents[t_name][t_EL][t_pot] = t_desc
    operator_info["talents"] = talents

    # Limited
    op_obtain_info = soup.find(class_="obtain-approach-table").text.strip()
    limited = re.search("LIMITED", op_obtain_info)

    operator_info["limited"] = True if limited else False

    # Free
    operator_info["free"] = False
    for item in soup.find_all("div", class_="approach-name"):
        if item.text.strip() in [
            "Activity Acquisition",
            "Event Reward",
            "Code Redemption",
            "Anniversary Reward",
            "Main Story"
        ]:
            operator_info["free"] = True

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
    if rarity == 1:
        archetype_info["archetype_name"] += " (1*)"

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

    # Archetype Cost Gains On Promotion
    e1_cost_gain = None
    e2_cost_gain = None
    if rarity > 2:
        e1_cost_gain = op_stat_object["e1"]["cost"] > op_stat_object["e0"]["cost"]
        if rarity > 3:
            e2_cost_gain = op_stat_object["e2"]["cost"] > op_stat_object["e1"]["cost"]
    archetype_info["cost_on_e1"] = e1_cost_gain
    archetype_info["cost_on_e2"] = e2_cost_gain

    # Archetype Block Gains On Promotion
    e1_block_gain = None
    e2_block_gain = None
    if rarity > 2:
        e1_block_gain = op_stat_object["e1"]["block"] > op_stat_object["e0"]["block"]
        if rarity > 3:
            e2_block_gain = op_stat_object["e2"]["block"] > op_stat_object["e1"]["block"]
    archetype_info["block_on_e1"] = e1_block_gain
    archetype_info["block_on_e2"] = e2_block_gain

    del op_stat_object["e0"]["cost"], op_stat_object["e0"]["block"]
    if rarity > 2:
        del op_stat_object["e1"]["cost"], op_stat_object["e1"]["block"]
        if rarity > 3:
            del op_stat_object["e2"]["cost"], op_stat_object["e2"]["block"]

    # Skill Info
    for cell in soup.findAll("div", class_="skill-cell"):
        skill = {}
        skill["skill_name"] = re.findall("Skill \d: (.+)", cell.text)[0]
        skill["sp_type"] = re.findall("SP Charge Type\n\n(.+)", cell.text)[0]
        skill["activation_type"] = re.findall(
            "Skill Activation\n\n\n(.+)", cell.text)[0]
        sp_cost_list = [item.text for item in cell.find(
            class_="sp-cost").findAll(class_="effect-description")]
        initial_sp_list = [item.text for item in cell.find(
            class_="initial-sp").findAll(class_="effect-description")]
        skill_duration_list = [item.text.strip() for item in cell.find(
            class_="skill-duration").findAll(class_="effect-description")]
        skill_description_list = cell.find(
            class_="skill-description").findAll(class_="effect-description")
        for skill_description in skill_description_list:
            for br in skill_description.select("br"):
                br.replace_with("\n")
            for rem in skill_description.findAll("span", class_="skill-description-rem"):
                rem.insert_before("\n")
        skill_description_list = [item.text.replace("\n\n", "\n").strip()
                                  for item in skill_description_list]
        skill_level_lookup = {
            0: "l1",
            1: "l2",
            2: "l3",
            3: "l4",
            4: "l5",
            5: "l6",
            6: "l7",
            7: "m1",
            8: "m2",
            9: "m3",
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

    # Tags
    tag_soup = soup.find(class_="tag-cell").findAll(class_="tag-title")
    tags = list(set([tag.text.strip() for tag in tag_soup]))

    # Modules
    module_soup = soup.findAll(class_="view-modules-on-operator")[1]
    mod_levels = module_soup.findAll(class_="views-row")[1:]
    for mod in mod_levels:
        m_name = mod.find(class_="module-title").text.strip().split("\n")[0]
        m_level = mod.find(
            class_="module-title"
        ).text.strip().split("\n")[1][-1]
        m_stat_lookup = {
            "max_hp": "HP",
            "atk": "ATK",
            "def": "DEF",
            "cost": "DP Cost",
            "attack_speed": "ASPD",
            "respawn_time": "Redeploy Time"
        }
        m_stats_table = mod.find("table").findAll("tr")[1:]
        m_stats = {
            m_stat_lookup.get(
                tr.find("th").text, tr.find("th").text
            ): int(tr.find("td").text) for tr in m_stats_table
        }
        if m_level == "1":
            m_trait = mod.find(class_="module-row-2")
            for item in m_trait.select("substitute"):
                item.replace_with("<Substitute>" + item.text)
            m_trait = m_trait.text.split("\n")[2]
            module = {
                "module_name": m_name,
                "level_1_trait_upgrade": m_trait,
                "level_1_stats": m_stats
            }
        else:
            m_t_soup = mod.find(
                class_="accordion-custom-content").findAll(class_="field__item")
            mod_talent = {}
            for t in m_t_soup:
                m_t_name = t.find(
                    class_="module-talent-name").text.strip()
                m_t_level = f"e2/l{rarity}0"
                m_t_pot = "pot"+t.find(
                    class_="module-talent-row-1").findAll("img")[1]["src"].split("/")[-1][0]
                m_t_desc = t.find(
                    class_="module-talent-row-2").text.strip()
                if not mod_talent.get(m_t_name):
                    mod_talent[m_t_name] = {m_t_level: {m_t_pot: m_t_desc}}
                else:
                    if not mod_talent[m_t_name].get(m_t_level):
                        mod_talent[m_t_name][m_t_level] = {m_t_pot: m_t_desc}
                    else:
                        mod_talent[m_t_name][m_t_level][m_t_pot] = m_t_desc
            module[f"level_{m_level}_stats"] = m_stats
            module[f"level_{m_level}_talent"] = mod_talent
        if m_level == "3":
            modules.append(module)
    return operator_info, archetype_info, skill_info, modules, tags


# if __name__ == "__main__":
    # pprint(scrape("eyjafjalla"))
    # scrape("archetto")
