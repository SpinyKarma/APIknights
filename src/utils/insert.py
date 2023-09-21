from pg8000.exceptions import DatabaseError
from copy import deepcopy
from src.utils.connect import connect, run
from src.utils.scraper import scrape
from src.utils.formatting import (
    select_query,
    insert_query,
    update_query,
    lit
)
from src.utils.debugger import Debug

log = Debug()
log.on()


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


def insert_archetype(archetype_info):
    ''' Take the archetype_info dict, compare it to the stored version, insert
        if not found. If found update if necessary, do nothing if not. Return
        the archetype_id from the stored version either from the query or after
        inserting.
    '''
    # Copy the dict to avoid mutation
    a_info = deepcopy(archetype_info)
    log("recieved info was ", a_info)
    # Extract the name for easy access
    a_name = a_info["archetype_name"]
    query = select_query("archetypes", "*", {"archetype_name": a_name})
    log("first query was", query)
    # Check for the stored version using the name to filter
    with connect() as db:
        stored = run(db, query)
    log("first response was", stored)
    # If found then extract the archetype_id
    if stored != []:
        log("something in storage")
        stored = stored[0]
        a_id = stored["archetype_id"]
        log("stored id was", a_id)
        # Compare the stored version with the current version
        updated = merge(stored, a_info)
        changes = {
            key: updated[key]
            for key in updated if updated[key] != stored.get(key)
        }
        # If any values need updating then run an update query
        if changes != {}:
            log("changes need making")
            query = update_query("archetypes", changes, {"archetype_id": a_id})
            log("second query was", query)
            with connect() as db:
                run(db, query)
            log("second response query was successful")
    # If not found then insert and return the assigned archetype_id
    else:
        log("nothing in storage")
        headings = [key for key in a_info]
        data = [a_info[key] for key in a_info]
        query = insert_query("archetypes", headings, data, "archetype_id")
        log("second query was", query)
        with connect() as db:
            res = run(db, query)[0]
        log("second response was", res)
        a_id = res["archetype_id"]
    # Return the archetype_id
    return a_id


def insert_module(module_info):
    ''' Take a module_info dict, query the stored version, insert if not found.
        If found skip. Return the module_id from the stored version either
        from the query or after inserting.
    '''
    # Copy the dict to avoid mutation
    m_info = deepcopy(module_info)
    # Extract the name for easy access
    m_name = m_info["module_name"]

    with connect() as db:
        # Check for the stored version using the name to filter
        query = f"SELECT * FROM modules WHERE module_name = {lit(m_name)};"
        stored = run(db, query)
        # If not found then insert and return the assigned module_id
        if stored == []:
            headings = [key for key in m_info]
            data = [m_info[key] for key in m_info]
            log(data)
            query = insert_query("modules", headings, data, ["module_id"])
            log(query)
            m_id = run(db, query)[0]["module_id"]
        # If found then extract the module_id
        else:
            stored = stored[0]
            log(f"module {m_name} already in db, skipping")
            m_id = stored["module_id"]
        log(m_info)
        return m_id


def insert_skill(skill_info):
    ''' Take a skill_info dict, query the stored version, insert if not found.
        If found skip. Return the skill_id from the stored version either
        from the query or after inserting.
    '''
    # Copy the dict to avoid mutation
    s_info = deepcopy(skill_info)
    # Extract the name for easy access
    s_name = s_info["skill_name"]
    with connect() as db:
        # Check for the stored version using the name to filter
        query = f"SELECT * FROM skills WHERE skill_name = {lit(s_name)};"
        stored = run(db, query)
        # If not found then insert and return the assigned skill_id
        if stored == []:
            headings = [key for key in s_info]
            data = [s_info[key] for key in s_info]
            log(data)
            query = insert_query("skills", headings, data, ["skill_id"])
            log(query)
            s_id = run(db, query)[0]["skill_id"]
        # If found then extract the skill_id
        else:
            stored = stored[0]
            log(f"skill {s_name} already in db, skipping")
            s_id = stored["skill_id"]
        log(s_info)
        return s_id


def insert_operator(operator_info, archetype_id, module_ids, skill_ids):
    ''' Take the operator_info dict, query the stored version, insert if not
        found. If operator has an alter and that alter is in the database,
        modify both to reflect that, if alter not found then make None.
        If operator found in db then skip. Return the operator_id from the
        stored version either from the query or after inserting.
    '''
    # Copy the dict to avoid mutation
    o_info = deepcopy(operator_info)
    # Extract the name for easy access
    o_name = o_info["operator_name"]
    with connect() as db:
        # Check for the stored version using the name to filter
        query = "SELECT * FROM operators WHERE "
        query += f"operator_name = {lit(o_name)};"
        stored = run(db, query)
        # If not found then insert and return the assigned operator_id
        if stored == []:
            alter_update = False
            log(archetype_id, module_ids, skill_ids)
            # Assign all the relevant ids to the operator before insertion
            o_info["archetype_id"] = archetype_id
            for i in range(len(module_ids)):
                o_info[f"module_{i+1}_id"] = module_ids[i][0]
            for i in range(len(skill_ids)):
                o_info[f"skill_{i+1}_id"] = skill_ids[i][0]
            alter = o_info.get("alter")
            # If the operator has a listed alter, query the db to find them
            if alter:
                query = "SELECT operator_id FROM operators "
                query += f"WHERE operator_name = {lit(alter)};"
                stored_alter = run(
                    db,
                )
                # If the alter isn't found then set alter to None on the op
                if stored_alter == []:
                    o_info["alter"] = None
                # Else take the alter's operator_id and flip a bool so the
                # alter's alter can be modified later to match
                else:
                    o_info["alter"] = stored_alter[0]["operator_id"]
                    alter_update = True
            # Insert the operator_info psot modification, returning the
            # assigned id
            headings = [key for key in o_info]
            data = [o_info[key] for key in o_info]
            log(headings)
            log("")
            log(data)
            query = insert_query("operators", headings, data, ["operator_id"])
            o_id = run(db, query)[0]["operator_id"]
            # If the bool was flipped earlier, then the alter needs it's alter
            # to reflect this operator now being in the db
            if alter_update:
                query = update_query(
                    "operators",
                    {"alter": o_id},
                    {"operator_id": o_info["alter"]}
                )
                run(db, query)
        # If found then extract the operator_id
        else:
            stored = stored[0]
            log(f"operator {o_name} already in db, skipping")
            o_id = stored["operator_id"]
        return o_id


def insert_tags(tag_info):
    tag_ids = []
    with connect() as db:
        stored = run(db, "SELECT * FROM tags;")
        stored_names = {tag[1]: tag[0] for tag in stored}
        for tag in tag_info:
            if tag in stored_names:
                tag_ids.append(stored_names[tag])
            else:
                query = insert_query("tags", "tag_name", tag, ["tag_id"])
                tag_id = run(db, query)[0]["tag_id"]
                tag_ids.append(tag_id)
    return tag_ids


def insert_operators_tags(o_id, tag_ids):
    with connect() as db:
        query = "SELECT tag_id FROM operators_tags WHERE "
        query += f"operator_id = {lit(o_id)};"
        stored = run(db, query)
        stored = [item[0] for item in stored]
        for tag in tag_ids:
            if tag not in stored:
                query = insert_query(
                    "operators_tags", ["operator_id", "tag_id"], [o_id, tag]
                )
                run(db, query)


def insert(operator_info, archetype_info, skill_info, tag_info, module_info):
    try:
        db = connect()
        db.close()
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
