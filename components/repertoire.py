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
        self.all_spells = {
            'heal': heal
        }
