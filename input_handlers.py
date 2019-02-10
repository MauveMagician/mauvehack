import libtcodpy as libtcod
from game_states import GameStates


def handle_keys(key, game_state):
    if game_state == GameStates.PLAYERS_TURN:
        return handle_player_turn_keys(key)
    elif game_state == GameStates.PLAYER_DEAD:
        return handle_player_dead_keys(key)
    elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.THROW_INVENTORY):
        return handle_inventory_keys(key)
    elif game_state == GameStates.CAST_SPELL:
        return handle_spellbook_keys(key)
    elif game_state == GameStates.TARGETING:
        return handle_targeting_keys(key)
    return {}


def handle_player_turn_keys(key):
    # Movement keys
    if key.vk == libtcod.KEY_UP:
        return {'move': (0, -1)}
    elif key.vk == libtcod.KEY_DOWN:
        return {'move': (0, 1)}
    elif key.vk == libtcod.KEY_LEFT:
        return {'move': (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT:
        return {'move': (1, 0)}
    elif key.vk == libtcod.KEY_SPACE:
        return {'take_stairs': True}
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
    elif chr(key.c) == 'i':
        return {'show_inventory': True}
    elif chr(key.c) == 'd':
        return {'drop_inventory': True}
    elif chr(key.c) == 't':
        return {'throw_inventory': True}
    elif chr(key.c) == 'a':
        return {'cast_spell': True}
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the game
        return {'exit': True}

    # No key was pressed
    return {}


def handle_targeting_keys(key):
    if key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    return {}


def handle_player_dead_keys(key):
    key_char = chr(key.c)
    if key_char == 'i':
        return {'show_inventory': True}
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {'exit': True}
    return {}


def handle_inventory_keys(key):
    index = key.c - ord('a')
    if index >= 0:
        return {'inventory_index': index}
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {'exit': True}
    return {}


def handle_spellbook_keys(key):
    index = key.c - ord('a')
    if index >= 0:
        return {'spellbook_index': index}
    if key.vk == libtcod.KEY_ENTER and key.lalt:
        # Alt+Enter: toggle full screen
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {'exit': True}
    return {}


def handle_mouse(mouse):
    (x, y) = (mouse.cx, mouse.cy)
    if mouse.lbutton_pressed:
        return {'left_click': (x, y)}
    elif mouse.rbutton_pressed:
        return {'right_click': (x, y)}
    return {}
