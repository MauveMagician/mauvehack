import libtcodpy as libtcod


def handle_keys(key):
    # Movement keys
    if key.vk == libtcod.KEY_UP:
        return {'move': (0, -1)}
    elif key.vk == libtcod.KEY_DOWN:
        return {'move': (0, 1)}
    elif key.vk == libtcod.KEY_LEFT:
        return {'move': (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT:
        return {'move': (1, 0)}
    elif chr(key.c) == 'y':
        return {'move': (-1, -1)}
    elif chr(key.c) == 'u':
        return {'move': (1, -1)}
    elif chr(key.c) == 'b':
        return {'move': (-1, 1)}
    elif chr(key.c) == 'n':
        return {'move': (1, 1)}
    if chr(key.c) == 'g':
        return {'pickup': True}

    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return {'exit': True}

    # No key was pressed
    return {}
