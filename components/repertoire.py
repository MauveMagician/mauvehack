import libtcodpy as libtcod


class Repertoire:
    def __init__(self):
        heal = {
            'char': '+',
            'color': libtcod.white,
            'name': 'Heal',
            'desc': 'Restores all your HP',
            'components': {
                'target': '"self"',
                'effect': 'HealSpell()'
            }
        }
        drain = {
            'char': '+',
            'color': libtcod.white,
            'name': 'Drain',
            'desc': 'Deals damage to all in line of sight, recovers 7 HP for each hit',
            'components': {
                'target': '"line_of_sight"',
                'effect': 'DrainSpell()'
            }
        }
        self.all_spells = {
            'heal': heal,
            'drain': drain
        }
