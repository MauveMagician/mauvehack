import libtcodpy as libtcod

class Artifactory:
    def __init__(self):

        dagger = {
            'char': '-',
            'color': libtcod.sky,
            'name': 'Dagger',
            'components': {
                'item': 'bool(True)',
                'power_bonus': '0',
                'dice': '"1d4"',
                'equip_type': '"main hand"',
                'equipped': 'False'
            }
        }
        healing_potion = {
            'char': '!',
            'color': libtcod.pink,
            'name': 'Potion of Healing',
            'components': {
                'item': 'bool(True)',
                'potion': 'Potion(effect=PotionHealing())'
            }
        }
        self.dungeon_artifactory = {
            'dagger': dagger,
            'healing_potion': healing_potion
        }