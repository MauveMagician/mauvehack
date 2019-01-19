import libtcodpy as libtcod

from game_messages import Message


class Fighter:
    def __init__(self, base_hp, base_defense, base_power):
        self.owner = None
        self.base_hp = base_hp
        self.hp = base_hp
        self.base_defense = base_defense
        self.base_power = base_power

    @property
    def max_hp(self):
        bonus = 0
        if self.owner and self.owner.components.get('equipped_items'):
            for c in self.owner.components['equipped_items']:
                if c.components.get('hp_bonus'):
                    bonus += c.components.get('hp_bonus')
        return self.base_hp + bonus

    @property
    def defense(self):
        bonus = 0
        if self.owner and self.owner.components.get('equipped_items'):
            for c in self.owner.components['equipped_items']:
                if c.components.get('def_bonus'):
                    bonus += c.components.get('def_bonus')
        return self.base_defense + bonus

    @property
    def power(self):
        bonus = 0
        if self.owner and self.owner.components.get('equipped_items'):
            for c in self.owner.components['equipped_items']:
                if c.components.get('power_bonus'):
                    bonus += c.components.get('power_bonus')
        return self.base_power + bonus

    def take_damage(self, amount):
        results = []
        self.hp -= amount
        if self.hp <= 0:
            results.append({'dead': self.owner})
        return results

    def attack(self, target):
        results = []
        if 'fighter' in target.components:
            damage = self.power - target.components['fighter'].defense
            if damage > 0:
                results.append({'message': Message('{0} attacks {1} for {2} hit points.'.format(
                    self.owner.name.capitalize(), target.name, str(damage)), libtcod.white)})
                results.extend(target.components['fighter'].take_damage(damage))
            else:
                results.append({'message': Message('{0} attacks {1} but does no damage.'.format(
                    self.owner.name.capitalize(), target.name), libtcod.white)})
        return results


class BasicMonster:
    def take_turn(self, target, fov_map, game_map, entities):
        results = []
        monster = self.owner
        if libtcod.map_is_in_fov(fov_map, monster.x, monster.y):
            if monster.distance_to(target) >= 2:
                monster.move_astar(target, entities, game_map)
            elif target.components['fighter'].hp > 0:
                attack_results = monster.components['fighter'].attack(target)
                results.extend(attack_results)
        return results


class Potion:
    def __init__(self, effect=None):
        self.effect = effect

    def used(self, user):
        return self.effect.apply(user)


class PotionEffect:
    def apply(self, user):
        return []


class PotionHealing(PotionEffect):
    def apply(self, user):
        results = []
        if user.components['fighter']:
            if user.components['fighter'].hp == user.components['fighter'].max_hp:
                results.append({'consumed': False, 'message': Message('You are already at full health', libtcod.yellow)})
            else:
                user.components['fighter'].hp = user.components['fighter'].max_hp
                results.append({'consumed': True, 'message': Message('Your wounds start to feel better!', libtcod.green)})
        return results


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []
        self.owner = None

    def add_item(self, item):
        results = []

        if len(self.items) >= self.capacity:
            results.append({
                'item_added': None,
                'message': Message('You cannot carry any more, your inventory is full', libtcod.yellow)
            })
        else:
            results.append({
                'item_added': item,
                'message': Message('You pick up the {0}!'.format(item.name), libtcod.blue)
            })
            item.x = -1
            item.y = -1
            self.items.append(item)
        return results

    def use(self, item_entity):
        results = []
        item_component = item_entity.components.get('potion')
        #if item_entity.components.get('potion') is None:
            #results.append({'message': Message('The {0} cannot be used'.format(item_entity.name), libtcod.yellow)})
        #else:
        if item_entity.components.get('potion') is not None:
            item_use_results = item_component.used(self.owner)
            for item_use_result in item_use_results:
                if item_use_result.get('consumed'):
                    self.remove_item(item_entity)
                    results.extend(item_use_results)
        elif item_entity.components.get('equip_type') is not None:
            if not item_entity.components.get('equipped'):
                results.extend(self.owner.components.get('inventory').equip(item_entity))
            else:
                results.extend(self.owner.components.get('inventory').dequip(item_entity))
        return results

    def remove_item(self, item):
        if item.components.get('equipped'):
            self.dequip(item)
        self.items.remove(item)

    def drop(self, item):
        results = []
        item.x = self.owner.x
        item.y = self.owner.y
        self.remove_item(item)
        results.append({'item_dropped': item, 'message': Message('You dropped the {0}'.format(item.name),
                                                                 libtcod.yellow)})
        return results

    def drop_all(self):
        for item in self.items:
            item.x = self.owner.x
            item.y = self.owner.y
            print("{0} dropped".format(item.name))
            self.remove_item(item)

    def equip(self, item):
        results = []
        if item in self.items:
            for i in self.owner.components.get('equipped_items'):
                    if i.components.get('equip_type') == item.components.get('equip_type'):
                        results = self.dequip(i)
            self.owner.components.get('equipped_items').append(item)
            item.components['equipped'] = True
            results.append({'item_equipped': item, 'message': Message('You equipped the {0}'.format(item.name),
                                                                      libtcod.light_chartreuse)})
        return results

    def dequip(self, item):
        results = []
        if item in self.items:
            self.owner.components.get('equipped_items').remove(item)
            item.components['equipped'] = False
            results.append({'item_dequipped': item, 'message': Message('You removed the {0}'.format(item.name),
                                                                       libtcod.light_chartreuse)})
        return results
