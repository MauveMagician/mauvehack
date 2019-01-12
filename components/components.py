import libtcodpy as libtcod

from game_messages import Message


class Fighter:
    def __init__(self, hp, defense, power):
        self.owner = None
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power

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
        return dict()


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
            self.items.append(item)
        return results

    def use(self, item_entity):
        results = []
        item_component = item_entity.components.get('potion')
        if item_entity.components.get('potion') is None:
            results.append({'message': Message('The {0} cannot be used'.format(item_entity.name), libtcod.yellow)})
        else:
            item_use_results = item_component.used(self.owner)
            print(item_use_results)
            for item_use_result in item_use_results:
                if item_use_result.get('consumed'):
                    self.remove_item(item_entity)
            results.extend(item_use_results)
        return results

    def remove_item(self, item):
        self.items.remove(item)
