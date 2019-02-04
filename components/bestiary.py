import libtcodpy as libtcod


class Bestiary:
    def __init__(self):

        orc = {
            'char': 'o',
            'color': libtcod.desaturated_green,
            'name': 'Orc',
            'components': {
                'fighter': 'Fighter(base_hp=15, base_defense=1, base_power=2)',
                'ai': 'BasicMonster()',
                'inventory': 'Inventory(capacity=26)',
                'equipped_items': "[]",
                'attack_effects': "[]",
                'status_effects': "[]"
            }
        }
        troll = {
            'char': 'T',
            'color': libtcod.darker_green,
            'name': 'Troll',
            'components': {
                'fighter': 'Fighter(base_hp=20, base_defense=1, base_power=1)',
                'ai': 'BasicMonster()',
                'status_effects': "[]"
            }
        }
        self.dungeon_bestiary = {
            'orc': orc,
            'troll': troll,
        }
