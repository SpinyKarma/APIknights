
''' Pseudo code for scraper func

    Args:
        operator name (format of gamepress url)

    Process:
        go to gamepress/operator name
        scrape:
            id "page title" for full operator name
            class "rarity-cell" for rarity
            class "profession-title" for class and archetype
            class "information-cell" for position and attack type
            class "alter-form" for alter operator
            class "range-title-cell" for each range for promotion levels
            class "description-box" for trait, description and quote in that order
            class "sub-title-type-1" for potentials and trust bonuses
            class "skill-section" for all skill info
            class "talent-child" for talents
            class "obtain-approach-table" for obtain approach info
            class "obtain-limited" to check if limited op
            class "tag-cell" for tag info
            var myStats from last script in first article for base and per-level stats
'''
