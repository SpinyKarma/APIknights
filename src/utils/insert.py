from pg8000.exceptions import DatabaseError
from copy import deepcopy
from src.utils.connect import connect, run
from src.utils.query import Query
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
        if old.get(key) == None:
            merged[key] = new[key]
        if new.get(key) == None:
            merged[key] = old[key]
        elif isinstance(new.get(key), dict) and isinstance(old.get(key), dict):
            merged[key] = merge(old[key], new[key])
        elif old.get(key) != new.get(key):
            merged[key] = new[key]
        else:
            merged[key] = old[key]
    return merged


def diff(before, after):
    changes = {
        key: after[key] for key in after if after[key] != before.get(key)
    }
    return changes


def insert_archetype(stored_arch_info, fresh_arch_info: dict):
    if stored_arch_info == []:
        query = Query("archetypes").insert_d(fresh_arch_info)
        query.returning("archetype_id")
        res = run(query())[0]
        a_id = res["archetype_id"]
    else:
        stored_arch_info = stored_arch_info[0]
        a_id = stored_arch_info["archetype_id"]
        merged = merge(stored_arch_info, fresh_arch_info)
        changes = diff(stored_arch_info, merged)
        if changes != {}:
            q = Query("archetypes").update(changes)
            q.where({"archetype_id": a_id})
            run(q())
    return a_id


def insert_skill(stored_skill_info, fresh_skill_info):
    if stored_skill_info == []:
        q = Query("skills").insert_d(fresh_skill_info).returning("skill_id")
        res = run(q())[0]
        s_id = res["skill_id"]
    else:
        stored_skill_info = stored_skill_info[0]
        s_id = stored_skill_info["skill_id"]
    return s_id


def insert_module(stored_mod_info, fresh_mod_info):
    if stored_mod_info == []:
        q = Query("modules").insert_d(fresh_mod_info).returning("module_id")
        res = run(q())[0]
        m_id = res["module_id"]
    else:
        stored_mod_info = stored_mod_info[0]
        m_id = stored_mod_info["module_id"]
    return m_id


def add_ids_to_op(fresh_op_info, a_id: int, s_ids: list, m_ids: list):
    id_fresh_op_info = deepcopy(fresh_op_info)
    id_fresh_op_info["archetype_id"] = a_id
    for i in range(len(m_ids)):
        id_fresh_op_info[f"module_{i+1}_id"] = m_ids[i]
    for i in range(len(s_ids)):
        id_fresh_op_info[f"skill_{i+1}_id"] = s_ids[i]
    if id_fresh_op_info.get("alter"):
        id_fresh_op_info["alter"] = None
    return id_fresh_op_info


def insert_operator(stored_op_info, id_fresh_op_info):
    if stored_op_info == []:
        q = Query("operators").insert_d(id_fresh_op_info)
        q.returning("operator_id")
        res = run(q())[0]
        o_id = res["operator_id"]
    else:
        stored_op_info = stored_op_info[0]
        o_id = stored_op_info["operator_id"]
    return o_id


def alter_mod(alter_name, o_id):
    if alter_name:
        q = Query("operators").select("operator_id")
        q.where({"operator_name": alter_name})
        res = run(q())
        if res != []:
            alter_id = res[0]["operator_id"]
            o_q = Query("operators").update({"alter": alter_id})
            o_q.where({"operator_id": o_id})
            a_q = Query("operators").update({"alter": o_id})
            a_q.where({"operator_id": alter_id})
            run(o_q)
            run(a_q)


def insert_tags(stored_tag_ids, fresh_tags):
    tag_ids = []
    for tag in fresh_tags:
        if tag not in stored_tag_ids:
            q = Query("tags").insert_d({"tag_name": tag}).returning("tag_id")
            res = run(q())[0]
            tag_ids.append(res["tag_id"])
        else:
            tag_ids.append(stored_tag_ids[tag])
    return tag_ids


def insert_operators_tags(stored_op_tag_ids, op_id, tag_ids):
    new_tags = [tag for tag in tag_ids if tag not in stored_op_tag_ids]
    for tag in new_tags:
        q = Query("operators_tags").insert_d(
            {"tag_id": tag, "operator_id": op_id}
        )
        run(q())


def insert(operator_info, archetype_info, skill_info, module_info, tag_info):
    try:
        connect()
    except DatabaseError as e:
        log.warn("Database doesn't exist yet, run 'reset-db.sh' to initialise")
        raise e
    a_q = Query("archetypes").select()
    a_q.where({"archetype_name": archetype_info["archetype_name"]})
    stored_a = run(a_q())
    a_id = insert_archetype(stored_a, archetype_info)

    s_ids = []
    for skill in skill_info:
        s_q = Query("skills").select()
        s_q.where({"skill_name": skill["skill_name"]})
        stored_s = run(s_q())
        s_ids.append(insert_skill(stored_s, skill))

    m_ids = []
    for module in module_info:
        m_q = Query("modules").select()
        m_q.where({"module_name": module["module_name"]})
        stored_m = run(m_q())
        m_ids.append(insert_module(stored_m, module))

    o_q = Query("operators").select()
    o_q.where({"operator_name": operator_info["operator_name"]})
    stored_o = run(o_q())
    modded_op_info = add_ids_to_op(operator_info, a_id, s_ids, m_ids)
    o_id = insert_operator(stored_o, modded_op_info)
    alter_mod(operator_info["alter"], o_id)

    t_q = Query("tags").select()
    stored_t = {tag["tag_name"]: tag["tag_id"] for tag in run(t_q())}
    t_ids = insert_tags(stored_t, tag_info)
    o_t_q = Query("operators_tags").select("tag_id")
    o_t_q.where({"operator_id": o_id})
    stored_o_t = [tag["tag_id"] for tag in run(o_t_q())]
    insert_operators_tags(stored_o_t, o_id, t_ids)


# if __name__ == "__main__":
    # from src.utils.scraper import scrape
    # insert(*scrape("cutter"))
    # query = select_query("operators", "operator_id, operator_name, alter")
    # log.x(run(query))
    # pass
