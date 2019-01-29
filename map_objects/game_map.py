import sys
from functools import partial

import pdb
from anytree import *
from components import dungeonfeatures as d
from components import components as c
from components import bestiary as b
from components import artifactory as a
import libtcodpy as libtcod

from random import randint, random, shuffle, choice

from game_messages import Message
from map_objects.rectangle import Rect
from map_objects.tile import Tile

from entity import Entity, build_monster_entity, build_item_entity, build_feature_entity, build_spell_entity

# noinspection PyMethodMayBeStatic,PyUnusedLocal
from render_functions import RenderOrder


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.dungeon_features = d.DungeonFeatures().standard_features
        self.bestiary = b.Bestiary().dungeon_bestiary
        self.artifactory = a.Artifactory().dungeon_artifactory
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()
        self.dungeon_level = dungeon_level
        self.generated_levels = dict()
        sys.setrecursionlimit(50000)

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
        return tiles

    '''Makes a default room and corridor map, it's not very structured'''
    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                 max_monsters_per_room, max_items_per_room):
        rooms = []
        num_rooms = 0

        center_of_last_room_x = None
        center_of_last_room_y = None

        for r in range(max_rooms):
            # random width and height
            w = randint(room_min_size, room_max_size) * 2
            h = randint(room_min_size, room_max_size) * 2
            # random position without going out of the boundaries of the map
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # run through the other rooms and see if they intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                # this means there are no intersections, so this room is valid

                # "paint" it to the map's tiles
                self.create_room(new_room)

                # center coordinates of new room, will be useful later
                (new_x, new_y) = new_room.center()

                center_of_last_room_x = new_x
                center_of_last_room_y = new_y

                if num_rooms == 0:
                    # this is the first room, where the player starts at
                    player.x = new_x
                    player.y = new_y
                else:
                    # all rooms after the first:
                    # connect it to the previous room with a tunnel
                    # center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()
                    if not self.check_connected(new_x, new_y, prev_x, prev_y, [], []):
                        # flip a coin (random number that is either 0 or 1)
                        if randint(0, 1) == 1:
                            try:
                                # first move horizontally, then vertically
                                self.create_h_tunnel(prev_x, new_x, prev_y)
                                self.create_v_tunnel(prev_y, new_y, new_x)
                            except DigException:
                                pass
                        else:
                            try:
                                # first move vertically, then horizontally
                                self.create_v_tunnel(prev_y, new_y, prev_x)
                                self.create_h_tunnel(prev_x, new_x, new_y)
                            except DigException:
                                pass
                self.place_entities(new_room, entities, max_monsters_per_room, max_items_per_room)
                rooms.append(new_room)
                num_rooms += 1
        self.finalize_dungeon(entities, player, center_of_last_room_x, center_of_last_room_y)

    '''Makes a cave level'''
    def make_cave(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                  max_monsters_per_room, max_items_per_room):
        for x in range(1, len(self.tiles)-1):
            for y in range(1, len(self.tiles[x])-1):
                if randint(0, 4) <= 1:
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False
                    self.tiles[x][y].components['type'] = 'floor'
                else:
                    pass
        self.cave_automaton_iterate()
        w = randint(room_min_size, room_max_size) * 2
        h = randint(room_min_size, room_max_size) * 2
        x = randint(0, map_width - w - 1)
        y = randint(0, map_height - h - 1)
        origin_room = Rect(x, y, w, h)
        destination_room = Rect(x, y, w, h)
        while destination_room.intersect(origin_room):
            dw = randint(room_min_size, room_max_size) * 2
            dh = randint(room_min_size, room_max_size) * 2
            dx = randint(0, map_width - dw - 1)
            dy = randint(0, map_height - dh - 1)
            destination_room = Rect(dx, dy, dw, dh)
        self.create_room(origin_room)
        self.create_room(destination_room)
        (origin_x, origin_y) = origin_room.center()
        (destination_x, destination_y) = destination_room.center()
        player.x = origin_x
        player.y = origin_y
        self.place_outside_entities(entities, max_monsters_per_room * 10, max_items_per_room * 5)
        self.place_entities(origin_room, entities, max_monsters_per_room, max_items_per_room)
        self.place_entities(destination_room, entities, max_monsters_per_room, max_items_per_room)
        success = self.finalize_dungeon(entities, player, destination_x, destination_y)
        if not success:
            try:
                self.create_v_tunnel(origin_y, destination_y, origin_x)
                self.create_h_tunnel(origin_x, destination_x, destination_y)
            except DigException:
                pass

    '''Iterates through tiles to open or close them up using the  rule'''
    def cave_automaton_iterate(self):
        for x in range(1, len(self.tiles)-1):
            for y in range(1, len(self.tiles[x])-1):
                wallcount = 0
                floorcount = 0
                if self.tiles[x+1][y].components.get('type') == 'floor':
                    floorcount += 1
                else:
                    wallcount += 1
                if self.tiles[x][y-1].components.get('type') == 'floor':
                    floorcount += 1
                else:
                    wallcount += 1
                if self.tiles[x][y+1].components.get('type') == 'floor':
                    floorcount += 1
                else:
                    wallcount += 1
                if self.tiles[x-1][y].components.get('type') == 'floor':
                    floorcount += 1
                else:
                    wallcount += 1
                if floorcount > wallcount:
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False
                    self.tiles[x][y].components['type'] = 'floor'
                elif wallcount < floorcount:
                    self.tiles[x][y].blocked = True
                    self.tiles[x][y].block_sight = True
                    self.tiles[x][y].components.clear()

    '''Make a dungeon level using BSP'''
    def make_bsp_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                     max_monsters_per_room, max_items_per_room):
        depth = 7
        min_size = room_min_size
        rooms = []
        bsp = libtcod.bsp_new_with_size(0, 0, map_width, map_height)
        libtcod.bsp_split_recursive(bsp, 0, depth, min_size + 1, min_size + 1, 1.5, 1.5)
        traverse_callback = partial(self.bsp_traverse_iterate, rooms=rooms)
        libtcod.bsp_traverse_inverted_level_order(bsp, traverse_callback, userData=1)
        destination = (0, 0)
        origin = rooms[0].center()
        player.x = origin[0]
        player.y = origin[1]
        for r in rooms:
            print(r.x1, r.y1, r.x2, r.y2)
            self.place_entities(r, entities, max_monsters_per_room * 50, max_items_per_room)
            destination = r.center()
        self.finalize_dungeon(entities, player, destination[0], destination[1])

    '''Call for each node of the BSP, creating rooms and corridors'''
    def bsp_traverse_iterate(self, bsp_node, data, rooms):
        bsp_rooms = rooms
        if libtcod.bsp_is_leaf(bsp_node):
            minx = bsp_node.x + 1
            maxx = bsp_node.x + bsp_node.w - 1
            miny = bsp_node.y + 1
            maxy = bsp_node.y + bsp_node.h - 1
            if maxx == self.width - 1:
                maxx -= 1
            if maxy == self.height - 1:
                maxy -= 1
            bsp_node.x = minx
            bsp_node.y = miny
            bsp_node.w = maxx - minx + 1
            bsp_node.h = maxy - miny + 1
            bsp_rooms.append(Rect(bsp_node.x, bsp_node.y, bsp_node.w, bsp_node.h))
            # Dig room
            for x in range(minx, maxx + 1):
                for y in range(miny, maxy + 1):
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False
                    self.tiles[x][y].components['type'] = 'room'
        else:
            left = libtcod.bsp_left(bsp_node)
            right = libtcod.bsp_right(bsp_node)
            bsp_node.x = min(left.x, right.x)
            bsp_node.y = min(left.y, right.y)
            bsp_node.w = max(left.x + left.w, right.x + right.w) - bsp_node.x
            bsp_node.h = max(left.y + left.h, right.y + right.h) - bsp_node.y
            if bsp_node.horizontal:
                if left.x + left.w - 1 < right.x or right.x + right.w - 1 < left.x:
                    x1 = libtcod.random_get_int(None, left.x, left.x + left.w - 1)
                    x2 = libtcod.random_get_int(None, right.x, right.x + right.w - 1)
                    y = libtcod.random_get_int(None, left.y + left.h, right.y)
                    self.vline_up(x1, y - 1)
                    self.hline(x1, y, x2)
                    self.vline_down(x2, y + 1)
                else:
                    minx = max(left.x, right.x)
                    maxx = min(left.x + left.w - 1, right.x + right.w - 1)
                    x = libtcod.random_get_int(None, minx, maxx)
                    # catch out-of-bounds attempts
                    while x > self.width - 1:
                        x -= 1
                    self.vline_down(x, right.y)
                    self.vline_up(x, right.y - 1)
            else:
                if left.y + left.h - 1 < right.y or right.y + right.h - 1 < left.y:
                    y1 = libtcod.random_get_int(None, left.y, left.y + left.h - 1)
                    y2 = libtcod.random_get_int(None, right.y, right.y + right.h - 1)
                    x = libtcod.random_get_int(None, left.x + left.w, right.x)
                    self.hline_left(x - 1, y1)
                    self.vline(x, y1, y2)
                    self.hline_right(x+1, y2)
                else:
                    miny = max(left.y, right.y)
                    maxy = min(left.y + left.h - 1, right.y + right.h - 1)
                    y = libtcod.random_get_int(None, miny, maxy)
                    # catch out-of-bounds attempts
                    while y > self.height - 1:
                        y -= 1
                    self.hline_left(right.x - 1, y)
                    self.hline_right(right.x, y)
        return True

    '''Make a battlefield-like level'''
    def make_bigroom_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                         max_monsters_per_room, max_items_per_room):
        for x in range(1, len(self.tiles)-1):
            for y in range(1, len(self.tiles[x])-1):
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False
                    self.tiles[x][y].components['type'] = 'floor'
        room = Rect(1, 1, map_width-2, map_height-2)
        downstairs_position = (randint(1, map_width-2), randint(1, map_height-2))
        upstairs_position = (randint(1, map_width-2), randint(1, map_height-2))
        while upstairs_position == downstairs_position:
            upstairs_position = (randint(1, map_width - 2), randint(1, map_height - 2))
        player.x = upstairs_position[0]
        player.y = upstairs_position[1]
        self.place_entities(room, entities, max_monsters_per_room * 50, max_items_per_room * 20)
        self.finalize_dungeon(entities, player, downstairs_position[0], downstairs_position[1])

    '''Make a maze level'''
    def make_maze_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                      max_monsters_per_room, max_items_per_room):
        explore_cells = []
        explored = []
        for x in range(1, len(self.tiles)-1):
            for y in range(1, len(self.tiles[x])-1):
                if x % 2 and y % 2:
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False
                    self.tiles[x][y].components['type'] = 'cell'
                    explore_cells.append((self.tiles[x][y], x, y))
        shuffle(explore_cells)
        x = 0
        y = 0
        backtrack = []
        current = explore_cells[0]
        number_cells_to_explore = len(explore_cells)
        while len(explored) < number_cells_to_explore:
            if current[0] not in explored:
                explored.append(current[0])
            x = current[1]
            y = current[2]
            possible = []
            if x - 2 >= 1:
                if not (self.tiles[x-2][y] in explored):
                    possible.append((self.tiles[x-2][y], -1, 0))
            if x + 2 < map_width-1:
                if not (self.tiles[x+2][y] in explored):
                    possible.append((self.tiles[x+2][y], +1, 0))
            if y - 2 >= 1:
                if not (self.tiles[x][y-2] in explored):
                    possible.append((self.tiles[x][y-2], 0, -1))
            if y + 2 < map_height - 1:
                if not (self.tiles[x][y+2] in explored):
                    possible.append((self.tiles[x][y+2], 0, +1))
            if possible:
                chosen_neighbor = choice(possible)
                self.tiles[x + (chosen_neighbor[1])][y + (chosen_neighbor[2])].blocked = False
                self.tiles[x + (chosen_neighbor[1])][y + (chosen_neighbor[2])].block_sight = False
                self.tiles[x + (chosen_neighbor[1])][y + (chosen_neighbor[2])].components['type'] = 'floor'
                current = (chosen_neighbor[0], x + (chosen_neighbor[1]*2), y + (chosen_neighbor[2]*2))
                backtrack.append(current)
            elif backtrack:
                current = backtrack.pop()
        player.x = x
        player.y = y
        last_x = x
        last_y = y
        while ((player.x, player.y) == (last_x, last_y)) or self.tiles[last_x][last_y].components.get('type') != 'cell':
            last_x = randint(1,map_width-1)
            last_y = randint(1, map_height-1)
        for x in range(1, len(self.tiles)-1):
            for y in range(1, len(self.tiles[x])-1):
                if self.tiles[x][y].components.get('type') == 'cell':
                    self.tiles[x][y].components['type'] = 'floor'
        self.place_outside_entities(entities, 20, 20)
        print(self.finalize_dungeon(entities, player, last_x, last_y))

    '''Finish making a dungeon'''
    def finalize_dungeon(self, entities, player, last_x, last_y):
        down_stairs = build_feature_entity(self.dungeon_features['downstairs'])
        down_stairs.components['stairs'].level = self.dungeon_level + 1
        down_stairs.spawn(last_x, last_y)
        up_stairs = build_feature_entity(self.dungeon_features['upstairs'])
        up_stairs.components['stairs'].level = self.dungeon_level - 1
        up_stairs.spawn(player.x, player.y)
        entities.append(down_stairs)
        entities.append(up_stairs)
        self.generated_levels[self.dungeon_level] = {'entities': entities, 'map': self.tiles}
        return self.check_connected(player.x, player.y, last_x, last_y, [], [])

    '''Solvability checker for dungeons'''
    def check_connected(self, x, y, prev_x, prev_y, explored=[], stack=[]):
        if x == prev_x and y == prev_y:
            return True
        explored.append(self.tiles[x][y])
        if self.tiles[x][y].components.get('type') == 'room' or self.tiles[x][y].components.get('type') == 'corridor' or self.tiles[x][y].components.get('type') == 'floor':
            try:
                if self.tiles[x + 1][y] not in explored:
                    stack.append([x + 1, y])
            except IndexError:
                pass
            try:
                if self.tiles[x][y - 1] not in explored:
                    stack.append([x, y - 1])
            except IndexError:
                pass
            try:
                if self.tiles[x][y + 1] not in explored:
                    stack.append([x, y + 1])
            except IndexError:
                pass
            try:
                if self.tiles[x - 1][y] not in explored:
                    stack.append([x - 1, y])
            except IndexError:
                pass
        if len(stack) > 0:
            tile_tuple = stack.pop()
            return self.check_connected(tile_tuple[0], tile_tuple[1], prev_x, prev_y, explored, stack)
        else:
            return False

    def create_room(self, room):
        # go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
                self.tiles[x][y].components['type'] = 'room'

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if not self.tiles[x][y].components.get('type') == 'room':
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
                self.tiles[x][y].components['type'] = 'corridor'
            elif self.tiles[x][y].components.get('type'):
                continue
            else:
                raise DigException()

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if not self.tiles[x][y].components.get('type') == 'room':
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
                self.tiles[x][y].components['type'] = 'corridor'
            elif self.tiles[x][y].components.get('type'):
                self.tiles[x][y].components['type'] = 'corridor'
                continue
            else:
                raise DigException()

    '''Vertical tunneling function for BSP'''
    def vline(self, x, y1, y2):
        if y1 > y2:
            y1, y2 = y2, y1
        for y in range(y1, y2 + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].components['type'] = 'corridor'

    def vline_up(self, x, y):
        while y >= 0 and self.tiles[x][y].blocked:
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].components['type'] = 'corridor'
            y -= 1

    def vline_down(self, x, y):
        while y < self.height and self.tiles[x][y].blocked:
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].components['type'] = 'corridor'
            y += 1

    '''Horizontal tunneling function for BSP'''
    def hline(self, x1, y, x2):
        if x1 > x2:
            x1, x2 = x2, x1
        for x in range(x1, x2 + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].components['type'] = 'corridor'

    def hline_left(self, x, y):
        while x >= 0 and self.tiles[x][y].blocked:
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].components['type'] = 'corridor'
            x -= 1

    def hline_right(self, x, y):
        while x < self.height and self.tiles[x][y].blocked:
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].components['type'] = 'corridor'
            x += 1

    def place_entities(self, room, entities, max_monsters_per_room, max_items_per_room):
        # Get a random number of monsters
        number_of_monsters = randint(0, max_monsters_per_room)
        # Get a random number of items
        number_of_items = randint(0, max_items_per_room)

        for i in range(number_of_monsters):
            # Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                if randint(0, 100) < 80:
                    monster = build_monster_entity(self.bestiary['orc'])
                    dagger = Entity('-', libtcod.sky, "Orc dagger", render_order=RenderOrder.ITEM,
                                    components={'item': bool(True),
                                                'power_bonus': 5,
                                                'equip_type': "main hand",
                                                'equipped': False
                                                })
                    monster.spawn(x, y)
                    monster.components['inventory'].add_item(dagger)
                    monster.components['inventory'].equip(dagger)
                    entities.append(dagger)
                else:
                    monster = build_monster_entity(self.bestiary['troll'])
                    monster.spawn(x, y)
                entities.append(monster)
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                if randint(0, 100) < 80:
                    item = build_item_entity(self.artifactory['healing_potion'])
                    item.spawn(x, y)
                else:
                    item = build_item_entity(self.artifactory['dagger'])
                    item.spawn(x, y)
                entities.append(item)

    def place_outside_entities(self, entities, max_monsters, max_items):
        # Get a random number of monsters
        number_of_monsters = randint(int(max_monsters/2), max_monsters)
        # Get a random number of items
        number_of_items = randint(int(max_items/2), max_items)
        for i in range(number_of_monsters):
            x = randint(1, 39)
            y = randint(1, 39)
            i = 0
            while (not self.tiles[x][y].components.get('type') == 'floor' or
                   self.tiles[x][y].components.get('type') == 'corridor') and i < 100:
                x = randint(1, 39)
                y = randint(1, 39)
                i += 1
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                if self.tiles[x][y].components.get('type'):
                    if randint(0, 100) < 80:
                        monster = build_monster_entity(self.bestiary['orc'])
                        dagger = Entity('-', libtcod.sky, "Orc dagger", render_order=RenderOrder.ITEM,
                                        components={'item': bool(True),
                                                    'power_bonus': 5,
                                                    'equip_type': "main hand",
                                                    'equipped': False
                                                    })
                        monster.spawn(x, y)
                        monster.components['inventory'].add_item(dagger)
                        monster.components['inventory'].equip(dagger)
                        entities.append(dagger)
                    else:
                        monster = build_monster_entity(self.bestiary['troll'])
                        monster.spawn(x, y)
                    entities.append(monster)
        for i in range(number_of_items):
            x = randint(1, 39)
            y = randint(1, 39)
            i = 0
            while (not self.tiles[x][y].components.get('type') == 'floor' or
                   self.tiles[x][y].components.get('type') == 'corridor') and i < 100:
                x = randint(1, 39)
                y = randint(1, 39)
                i += 1
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                if self.tiles[x][y].components.get('type'):
                    if randint(0, 100) < 80:
                        item = build_item_entity(self.artifactory['healing_potion'])
                        item.spawn(x, y)
                    else:
                        item = build_item_entity(self.artifactory['dagger'])
                        item.spawn(x, y)
                    entities.append(item)

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True
        return False

    def next_floor(self, player, message_log, constants):
        if not self.generated_levels.get(self.dungeon_level + 1):
            self.dungeon_level += 1
            entities = [player]
            self.tiles = self.initialize_tiles()
            self.make_cave(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                          constants['map_width'], constants['map_height'], player, entities,
                          constants['max_monsters_per_room'], constants['max_items_per_room'])
            message_log.add_message(Message('You descend into the next floor.', libtcod.light_violet))
            return entities
        else:
            self.dungeon_level += 1
            self.tiles = self.generated_levels.get(self.dungeon_level).get('map')
            for e in self.generated_levels.get(self.dungeon_level).get('entities'):
                if e.name == 'Stairs going up':
                    player.x = e.x
                    player.y = e.y
            message_log.add_message(Message('You go downstairs.', libtcod.light_violet))
            return self.generated_levels.get(self.dungeon_level).get('entities')

    def previous_floor(self, player, message_log, constants):
        if not self.generated_levels.get(self.dungeon_level - 1):
            self.dungeon_level -= 1
            entities = [player]
            self.tiles = self.initialize_tiles()
            self.make_cave(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
                          constants['map_width'], constants['map_height'], player, entities,
                          constants['max_monsters_per_room'], constants['max_items_per_room'])
            message_log.add_message(Message('You go into the next floor.', libtcod.light_violet))
            return entities
        else:
            self.dungeon_level -= 1
            self.tiles = self.generated_levels.get(self.dungeon_level).get('map')
            for e in self.generated_levels.get(self.dungeon_level).get('entities'):
                if e.name == 'Stairs going down':
                    player.x = e.x
                    player.y = e.y
            message_log.add_message(Message('You go upstairs.', libtcod.light_violet))
            return self.generated_levels.get(self.dungeon_level).get('entities')


class DigException(Exception):
    def __init__(self):
        pass
