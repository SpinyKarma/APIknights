from pg8000.exceptions import DatabaseError
from copy import deepcopy
from src.utils.connect import connect, run
# from src.utils.scraper import scrape
from src.utils.formatting import (
    select_query,
    insert_query,
    update_query,
    lit
)
from src.utils.debugger import Debug

log = Debug()
log.off()


def merge(old, new):
    ''' Take two dicts (old first), merges them, choosing which to take values
        from based on a particular ruleset.

        If either has a None value or missing a key, take from the other.
        If the value is a dict for both, recursively merge the dicts.
        If the values are different, take the value from the newer one.
        If they're the same, it doesn't matter which so take from older one.

        Args:
            old:
                The dict of the data pulled from the db, assumed older.
            new:
                The dict of the data waiting to be added to db, assumed newer.

        Returns:
            merged:
                The result of merging the two dicts according to above rules.
    '''
    merged = {}
    for key in set(list(new.keys())+list(old.keys())):
        log(key)
        if old.get(key) == None:
            log("overwriting Null value")
            merged[key] = new[key]
        if new.get(key) == None:
            log("keeping old value")
            merged[key] = old[key]
        elif isinstance(new.get(key), dict) and isinstance(old.get(key), dict):
            log(key+" is a dict")
            merged[key] = merge(old[key], new[key])
        elif old.get(key) != new.get(key):
            log("updating with new data")
            merged[key] = new[key]
        else:
            log("no change, keeing old")
            merged[key] = old[key]
    return merged


def diff(before, after):
    log(before, after)
    changes = {
        key: after[key] for key in after if after[key] != before.get(key)
    }
    return changes


def insert_archetype(stored_arch_info, fresh_arch_info):
    if stored_arch_info == []:
        query = insert_query("archetypes", fresh_arch_info, "archetype_id")
        res = run(query)[0]
        a_id = res["archetype_id"]
    else:
        stored_arch_info = stored_arch_info[0]
        a_id = stored_arch_info["archetype_id"]
        log("calling merge")
        merged = merge(stored_arch_info, fresh_arch_info)
        log("merged = ", merged)
        changes = diff(stored_arch_info, merged)
        log("changes = ", changes)
        if changes != {}:
            query = update_query("archetypes", changes, {"archetype_id": a_id})
            log("query = ", query)
            run(query)
            log("query has been run")
    return a_id


def insert_module(stored_mod_info, fresh_mod_info):
    if stored_mod_info == []:
        query = insert_query("modules", fresh_mod_info, "module_id")
        res = run(query)[0]
        m_id = res["module_id"]
    else:
        stored_mod_info = stored_mod_info[0]
        m_id = stored_mod_info["module_id"]
    return m_id


def insert_skill(stored_skill_info, fresh_skill_info):
    if stored_skill_info == []:
        query = insert_query("skills", fresh_skill_info, "skill_id")
        res = run(query)[0]
        s_id = res["skill_id"]
    else:
        stored_skill_info = stored_skill_info[0]
        s_id = stored_skill_info["skill_id"]
    return s_id


def add_ids_to_op(fresh_op_info, a_id: int, m_ids: list, s_ids: list):
    id_fresh_op_info = deepcopy(fresh_op_info)
    id_fresh_op_info["archetype_id"] = a_id
    for i in range(len(m_ids)):
        id_fresh_op_info[f"module_{i+1}_id"] = m_ids[i]
    for i in range(len(s_ids)):
        id_fresh_op_info[f"skill_{i+1}_id"] = s_ids[i]
    if id_fresh_op_info.get("alter"):
        del id_fresh_op_info["alter"]
    return id_fresh_op_info


def insert_operator(stored_op_info, id_fresh_op_info):
    if stored_op_info == []:
        query = insert_query("operators", id_fresh_op_info, "operator_id")
        res = run(query)[0]
        o_id = res["operator_id"]
    else:
        stored_op_info = stored_op_info[0]
        o_id = stored_op_info["operator_id"]
    return o_id


def alter_mod(alter_name, o_id):
    if alter_name:
        query = select_query(
            "operators", "operator_id", {"operator_name": alter_name}
        )
        res = run(query)
        if res != []:
            alter_id = res[0]["operator_id"]
            op_query = update_query(
                "operators", {"alter": alter_id}, {"operator_id": o_id}
            )
            alt_query = update_query(
                "operators", {"alter": o_id}, {"operator_id": alter_id}
            )
            run(op_query)
            run(alt_query)


def insert_tags(stored_tag_ids, fresh_tags):
    tag_ids = []
    for tag in fresh_tags:
        if tag not in stored_tag_ids:
            query = insert_query("tags", {"tag_name": tag}, "tag_id")
            res = run(query)[0]
            tag_ids.append(res["tag_id"])
        else:
            tag_ids.append(stored_tag_ids[tag])
    return tag_ids


def insert_operators_tags(stored_op_tag_ids, op_id, tag_ids):
    new_tags = [tag for tag in tag_ids if tag not in stored_op_tag_ids]
    for tag in new_tags:
        query = insert_query(
            "operators_tags", {"tag_id": tag, "operator_id": op_id}
        )
        run(query)


def insert(operator_info, archetype_info, skill_info, tag_info, module_info):
    try:
        connect()
    except DatabaseError as e:
        log.warn("Database doesn't exist yet, run 'seed-db.sh' to initialise.")
        raise e

    # Archetypes
    archetype_id = insert_archetype(archetype_info)
    log("Archetype ID: ", archetype_id, "\n")

    # Modules
    module_ids = []
    for mod in module_info:
        module_ids.append([insert_module(mod)])
    log("Module IDs: ", module_ids, "\n")

    # Skills
    skill_ids = []
    for skill in skill_info:
        skill_ids.append([insert_skill(skill)])
    log("Skill IDs: ", skill_ids, "\n")

    # Operators
    operator_id = insert_operator(
        operator_info,
        archetype_id,
        module_ids,
        skill_ids
    )
    log("Operator ID: ", operator_id, "\n")

    # Tags
    tag_ids = insert_tags(tag_info)
    log("Tag IDs: ", tag_ids)

    # Operators Tags
    insert_operators_tags(operator_id, tag_ids)


# if __name__ == "__main__":
    #     # insert(*scrape("blue-poison"))
    # with connect() as db:
    #     log(run(db, "SELECT * FROM archetypes WHERE archetype_name = 'banana';"))
