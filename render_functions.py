import libtcodpy as libtcod

from enum import Enum

from game_states import GameStates
from menus import inventory_menu, spellbook_menu


class RenderOrder(Enum):
    STRUCTURE = 1
    CORPSE = 2
    ITEM = 3
    ACTOR = 4


def render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, screen_width, screen_height,
               bar_width, panel_height, panel_y, mouse, colors, game_state):
    if fov_recompute:
        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = not (game_map.tiles[x][y].components.get('type'))
                if visible:
                    if wall:
                        libtcod.console_put_char_ex(con, x, y, '#', libtcod.white, libtcod.black)
                        if player.components.get('fatal').active:
                            libtcod.console_put_char_ex(con, x, y, '#', libtcod.dark_red, libtcod.black)
                    else:
                        libtcod.console_put_char(con, x, y, '.', libtcod.BKGND_NONE)
                        if player.components.get('fatal').active:
                            libtcod.console_put_char_ex(con, x, y, '.', libtcod.dark_red, libtcod.black)
                    game_map.tiles[x][y].explored = True
                elif game_map.tiles[x][y].explored:
                    if wall:
                        libtcod.console_put_char_ex(con, x, y, '#', libtcod.grey, libtcod.black)
                    else:
                        libtcod.console_put_char(con, x, y, ' ', libtcod.BKGND_NONE)
    entities_in_render_order = sorted(entities, key=lambda x: x.render_order.value)
    # Draw all entities in the list
    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map)
    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_print_ex(con, 1, screen_height - 2, libtcod.BKGND_NONE, libtcod.LEFT,
                             'HP: {0:02}<{1:02}>'.format(player.components['fighter'].hp,
                                                         player.components['fighter'].max_hp))
    libtcod.console_blit(con, 0, 0, screen_width, screen_height, 0, 0, 0)
    libtcod.console_set_default_background(panel, libtcod.black)
    libtcod.console_clear(panel)
    # Print the game messages, one line at a time
    y = 1
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.color)
        libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text)
        y += 1
    render_bar(panel, 1, 1, bar_width, 'HP', player.components['fighter'].hp,
               player.components['fighter'].max_hp, libtcod.light_red, libtcod.darker_red)
    libtcod.console_print_ex(panel, 1, 3, libtcod.BKGND_NONE, libtcod.LEFT,
                             'Dungeon level: {0}'.format(game_map.dungeon_level))
    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_mouse(mouse, entities, fov_map))
    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, 0, 0, panel_y)
    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'
        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)
    if game_state in (GameStates.CAST_SPELL, GameStates.FORGET_SPELL):
        if game_state == GameStates.CAST_SPELL:
            inventory_title = 'Press the key next to an ability to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an ability to forget it, or Esc to cancel.\n'
        spellbook_menu(con, inventory_title, player, 50, screen_width, screen_height)


def get_names_under_mouse(mouse, entities, fov_map):
    (x, y) = (mouse.cx, mouse.cy)
    names = [entity.name for entity in entities
             if entity.x == x and entity.y == y and libtcod.map_is_in_fov(fov_map, entity.x, entity.y)]
    names = ', '.join(names)
    return names.capitalize()


def render_bar(panel, x, y, total_width, name, value, maximum, bar_color, back_color):
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(panel, back_color)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(panel, bar_color)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER,
                             '{0}: {1}/{2}'.format(name, value, maximum))


def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)


def draw_entity(con, entity, fov_map, game_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or\
            (entity.components.get('structure') and game_map.tiles[entity.x][entity.y].explored):
        libtcod.console_set_default_foreground(con, entity.color)
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)


def clear_entity(con, entity):
    # erase the character that represents this object
    libtcod.console_put_char(con, entity.x, entity.y, ' ', libtcod.BKGND_NONE)
