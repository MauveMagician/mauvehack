import libtcodpy as libtcod
from components import components as c
from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_messages import MessageLog, Message
from game_states import GameStates
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all, RenderOrder

fov_radius = 10

max_monsters_per_room = 3
max_items_per_room = 3


def main():
    screen_width = 80
    screen_height = 50
    bar_width = 20
    panel_height = 7
    panel_y = screen_height - panel_height

    message_x = bar_width + 2
    message_width = screen_width - bar_width - 2
    message_height = panel_height - 1

    # Size of the map
    map_width = 80
    map_height = 40

    # Some variables for the rooms in the map
    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    fov_algorithm = 0
    fov_light_walls = True
    fov_radius = 10

    colors = {
        'white': libtcod.Color(255, 255, 255),
        'black': libtcod.Color(0, 0, 0)
    }
    player = Entity(0, 0, 1, libtcod.white, "Player", blocks=True, render_order=RenderOrder.ACTOR,
                    components={'fighter': c.Fighter(hp=10, defense=0, power=5),
                                'inventory': c.Inventory(capacity=26)})
    entities = [player]
    libtcod.console_set_custom_font('terminal8x8_gs_ro.png',
                                    libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
    libtcod.console_init_root(screen_width, screen_height, 'roguelike', False)
    con = libtcod.console_new(screen_width, screen_height)
    panel = libtcod.console_new(screen_width, panel_height)
    game_map = GameMap(map_width, map_height)
    game_map.make_map(max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                      max_monsters_per_room, max_items_per_room)
    fov_recompute = True
    fov_map = initialize_fov(game_map)
    message_log = MessageLog(message_x, message_width, message_height)
    key = libtcod.Key()
    mouse = libtcod.Mouse()
    game_state = GameStates.PLAYERS_TURN
    previous_game_state = game_state
    while not libtcod.console_is_window_closed():
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)
        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, fov_radius, fov_light_walls, fov_algorithm)
        render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, screen_width,
                   screen_height, bar_width, panel_height, panel_y, mouse, colors, game_state)
        libtcod.console_flush()
        clear_all(con, entities)
        action = handle_keys(key, game_state)
        move = action.get('move')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        inventory_index = action.get('inventory_index')
        exit = action.get('exit')
        fullscreen = action.get('fullscreen')
        player_turn_results = []
        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy
            if not game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)
                if target:
                    attack_results = player.components['fighter'].attack(target)
                    player_turn_results.extend(attack_results)
                else:
                    player.move(dx, dy)
                    fov_recompute = True
                game_state = GameStates.ENEMY_TURN
        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.components.get('item') and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.components['inventory'].add_item(entity)
                    player_turn_results.extend(pickup_results)
                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))
        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY
        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(
                player.components['inventory'].items):
            item = player.components['inventory'].items[inventory_index]
            player_turn_results.extend(player.components['inventory'].use(item))
        if exit:
            if game_state == GameStates.SHOW_INVENTORY:
                game_state = previous_game_state
            else:
                return True
        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            if message:
                message_log.add_message(message)
            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)
                message_log.add_message(message)
            if item_added:
                entities.remove(item_added)
                game_state = GameStates.ENEMY_TURN
            if item_consumed:
                game_state = GameStates.ENEMY_TURN
            elif not player_turn_result.get('consumed'):
                game_state = GameStates.PLAYERS_TURN
        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if 'ai' in entity.components.keys():
                    enemy_turn_results = (entity.components['ai'].take_turn(player, fov_map, game_map, entities))
                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')
                        if message:
                            message_log.add_message(enemy_turn_result.get('message'))
                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)
                            message_log.add_message(message)
                            if game_state == GameStates.PLAYER_DEAD:
                                break
                        if game_state == GameStates.PLAYER_DEAD:
                            break
            else:
                if game_state != GameStates.PLAYER_DEAD:
                    game_state = GameStates.PLAYERS_TURN


if __name__ == '__main__':
    main()
