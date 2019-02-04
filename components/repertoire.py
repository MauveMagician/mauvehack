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
        drain_beam = {
            'char': '+',
            'color': libtcod.white,
            'name': 'Bolt of Draining',
            'desc': 'Deals damage to all in line, recovers 7 HP for each hit',
            'components': {
                'target': '"beam"',
                'effect': 'DrainSpell()',
                'pierce': '5'
            }
        }
        swap = {
            'char': '+',
            'color': libtcod.white,
            'name': 'Swap Position',
            'desc': 'Swaps place with target',
            'components': {
                'target': '"target"',
                'effect': 'SwapSpell()'
            }
        }
        self.all_spells = {
            'heal': heal,
            'drain': drain,
            'swap': swap,
            'drain_beam': drain_beam
        }
