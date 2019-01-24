import libtcodpy as libtcod


class DungeonFeatures:
    def __init__(self):
        downstairs = {
            'char': '>',
            'color': libtcod.white,
            'name': 'Stairs going down',
            'components': {
                'structure': 'bool(True)',
                'stairs': 'Downstairs(0)'
            }
        }
        upstairs = {
            'char': '<',
            'color': libtcod.white,
            'name': 'Stairs going up',
            'components': {
                'structure': 'bool(True)',
                'stairs': 'Upstairs(0)'
            }
        }
        self.standard_features = {
            'downstairs': downstairs,
            'upstairs': upstairs
        }
