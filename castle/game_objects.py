class GameObject:
   def __init__(self, object_id, object_type, position):
       self.object_id = object_id
       self.object_type = object_type
       self.position = position

   def __repr__(self):
       return f"{self.__class__.__name__}(id={self.object_id}, position={self.position})"

class Castle(GameObject):
   def __init__(self, object_id, position, ally):
       super().__init__(object_id, 'structure', position)
       self.ally = ally

class Fighter(GameObject):
   def __init__(self, object_id, position, ally, name, is_ranged, fighter_type):
       super().__init__(object_id, 'unit', position)
       self.ally = ally
       self.name = name
       self.is_ranged = is_ranged
       self.fighter_type = fighter_type

class Knight(Fighter):
   def __init__(self, object_id, position, ally, name):
       super().__init__(object_id, position, ally, name,
                        is_ranged=False, fighter_type="knight")

class Archer(Fighter):
   def __init__(self, object_id, position, ally, name):
       super().__init__(object_id, position, ally, name,
                        is_ranged=True, fighter_type="archer")

class Wall(GameObject):
   def __init__(self, object_id, position):
       super().__init__(object_id, 'structure', position)
       self.ally = None


# command data + descriptions for agent, to control client
game_functions = [
   {
       'name': 'move_in_direction',
       'description': 'all units in unit_ids will move x_delta tiles to the right and y_delta tiles up. use this when moving to an empty space on the battlefield.',
       'args': {
           'unit_ids': {
               'description': 'a list of object_ids of the units you are selecting',
               'required': True
           },
           'x_delta': {
               'description': 'floating point number of how far right units will move (can be negative)',
               'required': True
           },
           'y_delta': {
               'description': 'floating point number of how far up units will move (can be negative)',
               'required': True
           }
       }
   },
   {
       'name': 'move_to_target',
       'description': 'all units in unit_ids will move to the target object. use this to move directly to a structure or unit.',
       'args': {
           'unit_ids': {
               'description': 'a list of object_ids of the units you are selecting',
               'required': True
           },
           'target_id': {
               'description': 'the object_id of the target (can be structure or another unit)',
               'required': True
           },
       }
   },
]


