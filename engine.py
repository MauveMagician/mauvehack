import libtcodpy as libtcod
import pickle
import pdb

from death_functions import kill_monster, kill_player
from entity import Entity, get_blocking_entities_at_location
from fov_functions import initialize_fov, recompute_fov
from game_messages import MessageLog, Message
from game_states import GameStates
from input_handlers import handle_keys
from map_objects.game_map import GameMap
from render_functions import clear_all, render_all, RenderOrder
from components import repertoire as r
from components import components as c
from entity import build_spell_entity

fov_radius = 100

max_monsters_per_room = 3
max_items_per_room = 3


def save_game(savename, entities, game_map, player, message_log, game_state):
    save_data = {
        "entities": entities,
        "game_map": game_map,
        "player": player,
        "message_log": message_log,
        "game_state": game_state
    }
    savefile = open(savename, 'rb+')
    pickle.dump(save_data, savefile)


def load_game(savefile):
    try:
        loaded = pickle.load(savefile)
        entities = loaded['entities']
        game_map = loaded['game_map']
        player = loaded['player']
        message_log = loaded['message_log']
        game_state = loaded['game_state']
        return False, entities, game_map, player, message_log, game_state
    except (EOFError, IOError, FileNotFoundError) as exeption:
        print("Couldn't find or load save file. Starting new game.")
        return True, None, None, None, None, None


def end_turn(entity):
    results = []
    effect_results = []
    for s in entity.components.get('status_effects'):
        try:
            s.timer_tick()
            effect_results.append(s.end_of_turn_effect())
        except:
            pass
    # Fatal (re)calculation
    if entity.components.get('fatal') and entity.components.get('fighter').hp > 0:
        if entity.components.get('fatal').active:
            message = entity.components.get('fatal').deactivate()
            print(message)
            results.append(message)
    for effect_result in effect_results:
        for result in effect_result:
            if result:
                results.append(result)
    return results


def main():
    savename = 'save.pkl'
    try:
        savefile = open(savename, 'rb+')
    except:
        savefile = open(savename, 'wb+')
    screen_width = 80
    screen_height = 50
    bar_width = 20
    panel_height = 7
    panel_y = screen_height - panel_height

    message_x = bar_width + 2
    message_width = screen_width - bar_width - 2
    message_height = panel_height - 1

    # Size of the map
    map_width = 40
    map_height = 40

    # Some variables for the rooms in the map
    room_max_size = 5
    room_min_size = 3
    max_rooms = 10

    fov_algorithm = 0
    fov_light_walls = True

    colors = {
        'white': libtcod.Color(255, 255, 255),
        'black': libtcod.Color(0, 0, 0)
    }
    repertoire = r.Repertoire().all_spells
    key = libtcod.Key()
    mouse = libtcod.Mouse()
    libtcod.console_set_custom_font('terminal8x8_gs_ro.png',
                                    libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_ASCII_INROW)
    libtcod.console_init_root(screen_width, screen_height, 'roguelike', False)
    con = libtcod.console_new(screen_width, screen_height)
    panel = libtcod.console_new(screen_width, panel_height)
    new_game, entities, game_map, player, message_log, game_state = load_game(savefile)
    if new_game:
        dagger = Entity('-', libtcod.sky, "Dagger", render_order=RenderOrder.ITEM,
                        components={'item': bool(True),
                                    'power_bonus': 0,
                                    'dice': '1d400',
                                    'equip_type': "main hand",
                                    'equipped': False
                                    })
        dagger2 = Entity('/', libtcod.sky, "Sword", render_order=RenderOrder.ITEM,
                        components={'item': bool(True),
                                    'power_bonus': 0,
                                    'dice': '1d8',
                                    'equip_type': "off hand",
                                    'equipped': False
                                    })
        heal = build_spell_entity(repertoire['heal'])
        drain = build_spell_entity(repertoire['drain'])
        player = Entity(1, libtcod.white, "Player", blocks=True, render_order=RenderOrder.ACTOR,
                        components={'fighter': c.Fighter(base_hp=20, base_defense=0, base_power=10),
                                    'inventory': c.Inventory(capacity=26),
                                    'equipped_items': [],
                                    'spellbook': c.Spellbook(capacity=26),
                                    'fatal': c.Fatal(7),
                                    'status_effects': []
                                    })
        player.components['status_effects'].append(c.Poison('poison', player, 25, 'pungent'))
        player.components['inventory'].add_item(dagger)
        player.components['inventory'].add_item(dagger2)
        player.components['inventory'].equip(dagger)
        player.components['inventory'].equip(dagger2)
        player.components['spellbook'].add_spell(heal)
        player.components['spellbook'].add_spell(drain)
        player.spawn(0, 0)
        entities = [player, dagger, dagger2]
        
        game_map = GameMap(map_width, map_height)
        game_map.make_cave(max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                            max_monsters_per_room, max_items_per_room)
        for e in entities:
            if e.name == 'Stairs going up':
                e.name = 'The gold-plated stairs of ascension'
                e.components['stairs'] = c.AscensionStairs()
                e.components['stairs'].owner = e
                e.color = libtcod.yellow
                break
        message_log = MessageLog(message_x, message_width, message_height)
        game_state = GameStates.PLAYERS_TURN
        previous_game_state = game_state
    fov_recompute = True
    fov_map = initialize_fov(game_map)
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
        drop_inventory = action.get('drop_inventory')
        inventory_index = action.get('inventory_index')
        take_stairs = action.get('take_stairs')
        cast_spell = action.get('cast_spell')
        cast_spell_index = action.get('spellbook_index')
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
                player_turn_results.extend(end_turn(player))
                if game_state != GameStates.PLAYER_DEAD:
                    game_state = GameStates.ENEMY_TURN
        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.components.get('item') and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.components['inventory'].add_item(entity)
                    player_turn_results.extend(pickup_results)
                    player_turn_results.extend(end_turn(player))
                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))
        if take_stairs and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.components.get('stairs') and entity.x == player.x and entity.y == player.y:
                    constants = {'max_rooms': max_rooms, 'room_min_size': room_min_size, 'room_max_size': room_max_size,
                                 'map_width': map_width, 'map_height': map_height,
                                 'entities': entities, 'max_monsters_per_room': max_monsters_per_room,
                                 'max_items_per_room': max_items_per_room
                                 }
                    try:
                        entities = entity.components.get('stairs').use(player, message_log, constants, game_map)
                    except c.CannotUseException:
                        pass
                    fov_map = initialize_fov(game_map)
                    fov_recompute = True
                    libtcod.console_clear(con)
                    player_turn_results.extend(end_turn(player))
                    break
            else:
                message_log.add_message(Message('There are no stairs here.', libtcod.yellow))
        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY
        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY
        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(
                player.components['inventory'].items):
            item = player.components['inventory'].items[inventory_index]
            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.components['inventory'].use(item))
                player_turn_results.extend(end_turn(player))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.components['inventory'].drop(item))
                player_turn_results.extend(end_turn(player))
        if cast_spell:
            previous_game_state = game_state
            game_state = GameStates.CAST_SPELL
        if cast_spell_index is not None and previous_game_state != GameStates.PLAYER_DEAD and cast_spell_index < len(
                player.components['spellbook'].spells):
            spell = player.components['spellbook'].spells[cast_spell_index]
            if game_state == GameStates.CAST_SPELL:
                player_turn_results.extend(player.components['spellbook'].cast(spell, entities=entities, fov_map=fov_map))
                player_turn_results.extend(end_turn(player))
        if exit:
            if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY, GameStates.CAST_SPELL):
                game_state = previous_game_state
            else:
                if game_state != GameStates.PLAYER_DEAD:
                    save_game(savename, entities, game_map, player, message_log, game_state)
                else:
                    open(savename, 'w')
                return True
        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())
        # End of turn cleanup
        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_dropped = player_turn_result.get('item_dropped')
            # Send messages to log
            if message:
                message_log.add_message(message)
            if dead_entity:
                if dead_entity == player:
                    if dead_entity.components.get('fatal'):
                        message, game_state = dead_entity.components.get('fatal').activate()
                    else:
                        message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity)
                message_log.add_message(message)
            # Add or remove items to the entities list
            if item_added:
                entities.remove(item_added)
            if item_dropped:
                entities.append(item_dropped)
            if game_state != GameStates.PLAYER_DEAD:
                game_state = GameStates.ENEMY_TURN
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
                                if dead_entity == player:
                                    if dead_entity.components.get('fatal'):
                                        message, game_state = dead_entity.components.get('fatal').activate()
                                    else:
                                        message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity)
                            message_log.add_message(message)
                            if game_state == GameStates.PLAYER_DEAD:
                                break
                        if game_state == GameStates.PLAYER_DEAD:
                            break
            if game_state != GameStates.PLAYER_DEAD:
                if player.components.get('fatal'):
                    if player.components.get('fatal').active:
                        player.components.get('fatal').count -= 1
                    game_state = GameStates.PLAYERS_TURN
        

if __name__ == '__main__':
    main()
