from castle.game_objects import Castle, Wall, Knight, Archer, Fighter, GameObject

# function to create objects from JSON that is sent in by client
def create_game_object(data):
    object_id = data['id']
    position = data['position']
    obj_type = data['type']


    if obj_type == 'structure':
        if 'ally' in data:  # Castle has an ally property
            return Castle(object_id, position, data['ally'])
        else:
            return Wall(object_id, position)
    elif obj_type == 'unit':
        ally = data['ally']
        name = data['name']
        is_ranged = data['isRanged']
        fighter_type = data['fighterType']
        if fighter_type == 'knight':
            return Knight(object_id, position, ally, name)
        elif fighter_type == 'archer':
            return Archer(object_id, position, ally, name)
        else:
            return Fighter(object_id, position, ally, name, is_ranged, fighter_type)
    else:
        print('WARNING creating unknown object', data)
        return GameObject(object_id, obj_type, position)  # Fallback
