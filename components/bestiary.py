import libtcodpy as libtcod
from entity import Entity
from render_functions import RenderOrder
from components.components import BasicMonster

class Bestiary:

    def __init__(self):

        orc = {
            'char':'o',
            'color': libtcod.desaturated_green,
            'name': 'Orc',
            'components': {
                'fighter': 'Fighter(hp=5, defense=1, power=1)',
                'ai': 'BasicMonster()'
            }
        }
        troll = {
            'char': 'T',
            'color': libtcod.darker_green,
            'name': 'Troll',
            'components': {
                'fighter': 'Fighter(hp=5, defense=1, power=1)',
                'ai': 'BasicMonster()'
            }
        }
        self.dungeon_bestiary = {
            'orc': orc,
            'troll': troll,
        }