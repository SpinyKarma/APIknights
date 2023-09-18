from pg8000.native import Connection, identifier as identifier, literal as literal
from dotenv import load_dotenv
from os import getenv
from scraper import scrape
from pg8000.exceptions import DatabaseError
from warn import warn, err
from pprint import pprint
import json


load_dotenv()

user = getenv("PGUSER")
password = getenv("PGPASSWORD")


def dict_res(res, dbcolumns):
    cols = [col["name"] for col in dbcolumns]
    return {cols[i]: res[0][i] for i in range(len(res[0]))}


def merge(stored, fresh):
    output = {}
    for key in set(list(fresh.keys())+list(stored.keys())):
        # print(key)
        if stored.get(key) == None:
            # print("overwriting Null value")
            output[key] = fresh[key]
        if fresh.get(key) == None:
            # print("keeping stored value")
            output[key] = stored[key]
        elif isinstance(fresh.get(key), dict):
            # print(key+" is a dict")
            output[key] = merge(stored[key], fresh[key])
        elif stored.get(key) != fresh.get(key):
            # print("updating with new data")
            output[key] = fresh[key]
        else:
            # print("no change, keeing stored")
            output[key] = stored[key]
    return output


def insert(operator_info, archetype_info, skill_info, tags, modules):
    try:
        db = Connection(user, database="apiknights", password=password)
    except DatabaseError as e:
        warn("Database does not exist yet, run 'seed-db.sh' to initialise.")
        raise e

    # Archetypes
    stored_A = db.run(
        f"SELECT * FROM archetypes WHERE archetype_name = {literal(archetype_info['archetype_name'])}")

    if stored_A != []:
        archetype_id = stored_A[0][0]
        stored_A = dict_res(stored_A, db.columns)
        updated_A = merge(stored_A, archetype_info)
        changes_A = [
            key for key in updated_A if updated_A[key] != stored_A[key]]
        if changes_A != []:
            print(
                f"change in {archetype_info['archetype_name']} archetype data")
            updated_A["ranges"] = json.dumps(updated_A["ranges"])
            data = ", ".join([f"{identifier(key)} = {literal(updated_A[key])}"
                              for key in changes_A])
            db.run(
                f"UPDATE archetypes SET {data} WHERE archetype_id = {literal(archetype_id)};")
        else:
            print(
                f"no change in {archetype_info['archetype_name']} archetype data")
    else:
        print(f"new archetype {archetype_info['archetype_name']}")
        headings_A = ', '.join([identifier(key) for key in archetype_info])
        # print(headings_A)
        archetype_info["ranges"] = json.dumps(archetype_info["ranges"])
        data = ", ".join([literal(archetype_info[key])
                          for key in archetype_info])
        # print(data)
        # print(literal(archetype_info["ranges"]))
        archetype_id = db.run(
            f"INSERT INTO archetypes ({headings_A}) VALUES ({data}) RETURNING archetype_id;")[0][0]

    # Modules
    mod_ids = {}
    for mod in modules:
        stored_M = db.run(
            f"SELECT * FROM modules WHERE module_name = {literal(mod['module_name'])};")
        if stored_M != []:
            print("module data already in db, skipping")
            # pprint(stored_M)
            mod_ids[stored_M[0][1]] = stored_M[0][0]
        else:
            headings_M = ', '.join([identifier(key) for key in mod])
            # print(headings_M)
            mod["level_1_stats"] = json.dumps(mod["level_1_stats"])
            mod["level_2_talent"] = json.dumps(mod["level_2_talent"])
            mod["level_2_stats"] = json.dumps(mod["level_2_stats"])
            mod["level_3_talent"] = json.dumps(mod["level_3_talent"])
            mod["level_3_stats"] = json.dumps(mod["level_3_stats"])
            data = ", ".join([literal(mod[key])for key in mod])
            # print(data)
            mod_id = db.run(
                f"INSERT INTO modules ({headings_M}) VALUES ({data}) RETURNING module_id;")[0][0]
            mod_ids[mod["module_name"]] = mod_id
    print(mod_ids)

    # Skills
    skill_ids = {}
    for skill in skill_info:
        stored_S = db.run(
            f"SELECT * FROM skills WHERE skill_name = {literal(skill['skill_name'])};")
        if stored_S != []:
            print("skill data already in db, skipping")
            # pprint(stored_S)
            skill_ids[stored_S[0][1]] = stored_S[0][0]
        else:
            headings_S = ', '.join([identifier(key) for key in skill])
            # print(headings_S)
            skill["l1"] = json.dumps(skill["l1"])
            skill["l2"] = json.dumps(skill["l2"])
            skill["l3"] = json.dumps(skill["l3"])
            skill["l4"] = json.dumps(skill["l4"])
            skill["l5"] = json.dumps(skill["l5"])
            skill["l6"] = json.dumps(skill["l6"])
            skill["l7"] = json.dumps(skill["l7"])
            if skill.get("m1"):
                skill["m1"] = json.dumps(skill["m1"])
            if skill.get("m2"):
                skill["m2"] = json.dumps(skill["m2"])
            if skill.get("m3"):
                skill["m3"] = json.dumps(skill["m3"])
            data = ", ".join([literal(skill[key])for key in skill])
            # print(data)
            skill_id = db.run(
                f"INSERT INTO skills ({headings_S}) VALUES ({data}) RETURNING skill_id;")[0][0]
            skill_ids[skill["skill_name"]] = skill_id
    print(skill_ids)

    # Tags
    op_tag_ids = []
    stored_T = db.run(
        f"SELECT * FROM tags;")
    stored_T_names = {tag[1]: tag[0] for tag in stored_T}
    for tag in tags:
        if tag in stored_T_names:
            op_tag_ids.append(stored_T_names[tag])
        else:
            tag_id = db.run(
                f"INSERT INTO tags (tag_name) VALUES ({literal(tag)}) RETURNING tag_id;")[0][0]
            op_tag_ids.append(tag_id)
    pprint(stored_T_names)
    print(op_tag_ids)

    # Operators
    # query operators table for op using operator_info["operator_name"]
    # if exists:
    #   skip (in future: compare and update if necessary)
    #   grab op_id from query
    # else:
    #   substitute archetype/module/skill names for ids using archetype_id, skill_ids, mod_ids
    #   dump all json keys
    #   insert, returning op_id

    # Tags
    # query operators_tags table for ops tags using op_id
    # for each tag relation in op_tag_ids:
    #   if exists in query result:
    #     skip
    #   else:
    #     insert


if __name__ == "__main__":
    insert(*scrape("kroos"))
