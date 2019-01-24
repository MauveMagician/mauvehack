class Tile:
    """
    A tile on a map. It may or may not be blocked, and may or may not block sight.
    """
    def __init__(self, blocked, block_sight=None, components=None):
        self.blocked = blocked
        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight
        self.explored = False
        self.components = components
        if components:
            for component in components.values():
                try:
                    component.owner = self
                except AttributeError:
                    pass
        else:
            self.components = dict()
