import libtcodpy as libtcod
import dice
import death_functions
import pdb

from game_messages import Message
from game_states import GameStates


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

    @property
    def damage_dice(self):
        bonus = []
        if self.owner and self.owner.components.get('equipped_items'):
            for c in self.owner.components['equipped_items']:
                if c.components.get('dice'):
                    bonus.append(c.components.get('dice'))
        return bonus

    def take_damage(self, amount, **kwargs):
        results = []
        self.hp -= amount
        if self.hp <= 0:
            results.append({'dead': self.owner})
        return results

    def restore_health(self, amount):
        results = []
        if self.hp < 0:
            self.hp = 0
        self.hp = min((self.hp+amount), self.max_hp)
        results.append({'message': Message('{0} recovers {1} hit points'.format(
            self.owner.name.capitalize(), amount), libtcod.green
        )})
        return results

    def attack(self, target):
        results = []
        if 'fighter' in target.components:
            damage_roll = 0
            for d in self.damage_dice:
                damage_roll += dice.roll(d)
            damage = self.power + damage_roll - target.components['fighter'].defense
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
            else:
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
                results.append(
                    {'message': Message('You drink the potion, but are already at full health, nothing happens', libtcod.yellow)})
            else:
                user.components['fighter'].hp = user.components['fighter'].max_hp
                results.append(
                    {'message': Message('Your wounds start to feel better!', libtcod.green)})
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
        if item_entity.components.get('potion') is not None:
            item_use_results = item_component.used(self.owner)
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


class Downstairs:
    def __init__(self, level):
        self.level = level
        self.owner = None

    def use(self, player, message_log, constants, game_map):
        return game_map.next_floor(player, message_log, constants)


class Upstairs:
    def __init__(self, level):
        self.level = level
        self.owner = None

    def use(self, player, message_log, constants, game_map):
        return game_map.previous_floor(player, message_log, constants)


class CannotUseException(Exception):
    def __init__(self):
        pass


class AscensionStairs:
    def __init__(self):
        self.owner = None

    def use(self, player, message_log, constants, game_map):
        if player.components.get('ascend'):
            pass
        else:
            message_log.add_message(Message('The dungeon prevents tributes from escaping without the' +
                                            ' blessing of ascension. Remember who you are, and your purpose.',
                                            libtcod.yellow))
            raise CannotUseException()


class Fatal:
    def __init__(self, count_max):
        self.count_max = count_max
        self.count = count_max
        self.active = False
        self.owner = None

    def activate(self):
        if not self.active:
            self.active = True
            return Message('You feel the grasp of death upon your soul! Mend your wounds or face your fate!',
                           libtcod.pink), None
        else:
            death_roll = dice.roll("1d6")
            print(self.count, death_roll)
            if death_roll >= self.count:
                death_functions.kill_player(self.owner)
                return Message('You died!', libtcod.red), GameStates.PLAYER_DEAD
            return Message('You survived, but your time may yet arrive!', libtcod.red), None

    def deactivate(self):
        self.count = self.count_max
        self.active = False
        return {'message': Message('You no longer feel the reaper', libtcod.light_pink)}


class Spellbook:
    def __init__(self, capacity):
        self.capacity = capacity
        self.spells = []
        self.owner = None

    def add_spell(self, spell):
        results = []
        if len(self.spells) >= self.capacity:
            results.append({
                'item_added': None,
                'message': Message('You cannot learn any new tricks.', libtcod.yellow)
            })
        else:
            results.append({
                'spell_added': spell,
                'message': Message('You learned {0}!'.format(spell.name), libtcod.cyan)
            })
            self.spells.append(spell)
        return results

    def cast(self, spell, **kwargs):
        results = [{'cast': True}]
        if spell.components.get('target') == 'self':
            spell_cast_results = spell.components['effect'].cast(self.owner)
            for cast_result in spell_cast_results:
                results.append(cast_result)
        elif spell.components.get('target') == 'line_of_sight':
            entities = kwargs.get('entities')
            fov_map = kwargs.get('fov_map')
            spell_cast_results = []
            for e in entities:
                if libtcod.map_is_in_fov(fov_map, e.x, e.y):
                    spell_cast_results.append(spell.components['effect'].cast(self.owner, e))
            for cast_result in spell_cast_results:
                for result in cast_result:
                    if result:
                        results.append(result)
        return results


class HealSpell:
    def cast(self, user):
        results = []
        if user.components['fighter']:
                user.components['fighter'].hp = user.components['fighter'].max_hp
                pass
                results.append({'message': Message('Your wounds start to feel better!', libtcod.green)})
        return results


class DrainSpell:
    def cast(self, user, target):
        u = user.components.get('fighter')
        t = target.components.get('fighter')
        results = []
        if u and t and u is not t:
            damage = dice.roll('2d12')
            results.append({'message': Message('{0} is drained for {1} hit points.'.format(
                target.name, str(damage)), libtcod.white)})
            results.extend(t.take_damage(damage))
            results.extend(u.restore_health(7))
        return results


class StatusEffect:
    def __init__(self, name, owner, timer=50):
        self.name = name
        self.owner = owner
        self.timer = timer

    def timer_tick(self):
        self.timer -= 1
        if self.timer <= 0:
            self.end()

    def end(self):
        self.owner.components.get('status_effects').remove(self)
        self.owner = None


class Poison(StatusEffect):
    def __init__(self, name, owner, value, flavor, timer=50):
        super().__init__(name, owner, timer)
        self.value = value
        self.flavor = flavor
        if self.owner.components:
            flag = False
            for s in self.owner.components.get('status_effects'):
                if s.__class__.__name__ == 'Poison' and s is not self:
                    s.value += value
                    flag = True
            if flag:
                self.owner.components.get('status_effects').remove(self)

    def end_of_turn_effect(self):
        results = []
        if self.owner.components.get('fighter'):
            poison_damage = max(1, int(self.value/5))
            self.value -= poison_damage
            results.append({'message': Message('The {0} poison saps {1} for {2} hit points.'.format(
                self.flavor, self.owner.name, str(poison_damage)), libtcod.dark_green)})
            results.extend(self.owner.components.get('fighter').take_damage(poison_damage, type='poison'))
            if self.value <= 0:
                self.end()
        return results
