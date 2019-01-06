import libtcodpy as libtcod


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
                results.append({'message': '{0} attacks {1} for {2} hit points.'.format(
                    self.owner.name.capitalize(), target.name, str(damage))})
                results.extend(target.components['fighter'].take_damage(damage))
            else:
                results.append({'message': '{0} attacks {1} but does no damage.'.format(
                    self.owner.name.capitalize(), target.name)})
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
