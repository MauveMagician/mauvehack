from components import dungeonfeatures as d
from components import components as c
from components import bestiary as b
from components import artifactory as a
import libtcodpy as libtcod

from random import randint

from game_messages import Message
from map_objects.rectangle import Rect
from map_objects.tile import Tile

from entity import Entity, build_monster_entity, build_item_entity, build_feature_entity

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

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
        return tiles

    def make_map(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                 max_monsters_per_room, max_items_per_room):
        rooms = []
        num_rooms = 0

        center_of_last_room_x = None
        center_of_last_room_y = None

        for r in range(max_rooms):
            # random width and height
            w = randint(room_min_size, room_max_size)*2
            h = randint(room_min_size, room_max_size)*2
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
                # finally, append the new room to the list
                self.place_entities(new_room, entities, max_monsters_per_room, max_items_per_room)
                rooms.append(new_room)
                num_rooms += 1
        down_stairs = build_feature_entity(self.dungeon_features['downstairs'])
        down_stairs.components['stairs'].level = self.dungeon_level + 1
        down_stairs.spawn(center_of_last_room_x, center_of_last_room_y)
        up_stairs = build_feature_entity(self.dungeon_features['upstairs'])
        up_stairs.components['stairs'].level = self.dungeon_level - 1
        up_stairs.spawn(player.x, player.y)
        entities.append(down_stairs)
        entities.append(up_stairs)
        print(self.check_connected(player.x, player.y, center_of_last_room_x, center_of_last_room_y, [], []))
        self.generated_levels[self.dungeon_level] = {'entities': entities, 'map': self.tiles}

    def make_map_bsp(self, max_rooms, room_min_size, room_max_size, map_width, map_height, player, entities,
                 max_monsters_per_room, max_items_per_room):

        down_stairs = build_feature_entity(self.dungeon_features['downstairs'])
        down_stairs.components['stairs'].level = self.dungeon_level + 1
        down_stairs.spawn(0, 0)
        up_stairs = build_feature_entity(self.dungeon_features['upstairs'])
        up_stairs.components['stairs'].level = self.dungeon_level - 1
        up_stairs.spawn(player.x, player.y)
        entities.append(down_stairs)
        entities.append(up_stairs)
        self.generated_levels[self.dungeon_level] = {'entities': entities, 'map': self.tiles}

    def check_connected(self, x, y, prev_x, prev_y, explored=[], stack=[]):
        if x == prev_x and y == prev_y:
            return True
        explored.append(self.tiles[x][y])
        if self.tiles[x][y].components.get('type') == 'room' or self.tiles[x][y].components.get('type') == 'corridor':
            try:
                if self.tiles[x+1][y-1] not in explored:
                    stack.append([x+1, y-1])
            except IndexError:
                pass
            try:
                if self.tiles[x+1][y] not in explored:
                    stack.append([x+1, y])
            except IndexError:
                pass
            try:
                if self.tiles[x+1][y+1] not in explored:
                    stack.append([x+1, y+1])
            except IndexError:
                pass
            try:
                if self.tiles[x][y-1] not in explored:
                    stack.append([x, y-1])
            except IndexError:
                pass
            try:
                if self.tiles[x][y+1] not in explored:
                    stack.append([x, y+1])
            except IndexError:
                pass
            try:
                if self.tiles[x-1][y-1] not in explored:
                    stack.append([x-1, y-1])
            except IndexError:
                pass
            try:
                if self.tiles[x-1][y] not in explored:
                    stack.append([x-1, y])
            except IndexError:
                pass
            try:
                if self.tiles[x-1][y+1] not in explored:
                    stack.append([x-1, y+1])
            except IndexError:
                pass
            if stack:
                print(stack)
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
                if self.tiles[x][y].components.get('type') is None:
                    self.tiles[x][y].components['type'] = 'corridor'
            elif self.tiles[x][y].components.get('type') == 'room':
                continue
            else:
                raise DigException()

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if not self.tiles[x][y].components.get('type') == 'room':
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False
                if self.tiles[x][y].components.get('type') is None:
                    self.tiles[x][y].components['type'] = 'corridor'
            elif self.tiles[x][y].components.get('type') == 'room':
                continue
            else:
                raise DigException()

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
                    dagger = Entity('-',      libtcod.sky, "Orc dagger", render_order=RenderOrder.ITEM,
                                    components={'item': bool(True),
                                                'power_bonus': 5,
                                                'equip_type': "main hand",
                                                'equipped': False
                                                })
                    monster.spawn(x,y)
                    monster.components['inventory'].add_item(dagger)
                    monster.components['inventory'].equip(dagger)
                    entities.append(dagger)
                else:
                    monster = build_monster_entity(self.bestiary['troll'])
                    monster.spawn(x,y)
                entities.append(monster)
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                if randint(0, 100) < 80:
                    item = build_item_entity(self.artifactory['healing_potion'])
                    item.spawn(x,y)
                else:
                    item = build_item_entity(self.artifactory['dagger'])
                    item.spawn(x,y)                    
                entities.append(item)

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True
        return False

    def next_floor(self, player, message_log, constants):
        if not self.generated_levels.get(self.dungeon_level+1):
            self.dungeon_level += 1
            entities = [player]
            self.tiles = self.initialize_tiles()
            self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
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
        if not self.generated_levels.get(self.dungeon_level-1):
            self.dungeon_level -= 1
            entities = [player]
            self.tiles = self.initialize_tiles()
            self.make_map(constants['max_rooms'], constants['room_min_size'], constants['room_max_size'],
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
