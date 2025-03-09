from __future__ import annotations
from abc import ABC


class Effect(ABC):
    def __init__(self, effect_power: int = 0):
        self.effect_name: str = ''
        self.use_on: str = ''
        self.parameter: str = ''
        self.state: str = ''
        self.effect_power: int = effect_power

    def __str__(self):
        return self.effect_name


class UseEnergy(Effect):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.effect_name: str = 'use_energy'
        self.use_on: str = 'self'
        self.parameter: str = 'energy'
        self.state: str = 'sub'


class GainEnergy(Effect):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.effect_name: str = 'gain_energy'
        self.use_on: str = 'self'
        self.parameter: str = 'energy'
        self.state: str = 'add'


class Damage(Effect):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.effect_name: str = 'damage'
        self.use_on: str = 'enemy'
        self.parameter: str = 'health'
        self.state: str = 'sub'


class Block(Effect):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.effect_name: str = 'block'
        self.use_on: str = 'self'
        self.parameter: str = 'health'
        self.state: str = 'mul'


class EnergyPenalty(Effect):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.effect_name: str = 'energy_penalty'
        self.use_on: str = 'enemy'
        self.parameter: str = 'energy'
        self.state: str = 'mul'


class Stun(Effect):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.effect_name: str = 'stun'
        self.use_on: str = 'enemy'
        self.parameter: str = 'skip'
        self.state: str = 'true'


class EffectsFactory:
    effect_classes: dict[str, type[Effect]] = {
        'use_energy': UseEnergy,
        'gain_energy': GainEnergy,
        'damage': Damage,
        'block': Block,
        'energy_penalty': EnergyPenalty,
        'stun': Stun,
    }

    @classmethod
    def create_effect(cls, effect_name: str, **kwargs) -> Effect:
        effect_class = cls.effect_classes.get(effect_name)
        if effect_class:
            return effect_class(**kwargs)
        else:
            raise ValueError(f'Unknown effect: {effect_name}')


class Action(ABC):
    def __init__(self, energy_cost: int = 0, action_power: int = 0) -> None:
        self.action_name: str = ''
        self.energy_cost: int = energy_cost
        self.action_power: int = action_power
        self.effects: dict[str, Effect] = {}
        self.counter_actions: dict[str, dict[str, Effect]] = {}

    def __str__(self) -> str:
        return self.action_name

    @staticmethod
    def resolve_actions(left_action: Action, right_action: Action):
        actions = (left_action, right_action)
        status = (Status(), Status())

        for index, action in enumerate(actions):
            for effect_name, effect in action.effects.items():
                if effect.use_on == 'self':
                    status[index].apply_effect(effect)
                elif effect.use_on == 'enemy':
                    status[not index].apply_effect(effect)

            if action.action_name in actions[not index].counter_actions:
                for counter_effect_name, counter_effect in (
                        actions[not index].counter_actions[action.action_name].items()):

                    if counter_effect.use_on == 'self':
                        status[not index].apply_effect(counter_effect)
                    elif counter_effect.use_on == 'enemy':
                        status[index].apply_effect(counter_effect)

        return status


class Attack(Action):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.action_name: str = 'attack'
        self.effects['use_energy'] = EffectsFactory.create_effect(effect_name='use_energy',
                                                                  effect_power=self.energy_cost)

        self.effects['damage'] = EffectsFactory.create_effect(effect_name='damage',
                                                              effect_power=self.action_power)


class Defence(Action):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.action_name: str = 'defence'
        self.effects['use_energy'] = EffectsFactory.create_effect(effect_name='use_energy',
                                                                  effect_power=self.energy_cost)
        self.counter_actions['attack'] = {
            'block': EffectsFactory.create_effect(effect_name='block',
                                                  effect_power=0),
            'energy_penalty': EffectsFactory.create_effect(effect_name='energy_penalty',
                                                           effect_power=2),
            'stun': EffectsFactory.create_effect(effect_name='stun',
                                                 effect_power=0),
        }


class Feint(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.action_name: str = 'feint'
        self.counter_actions['defence'] = {
            'energy_penalty': EffectsFactory.create_effect(effect_name='energy_penalty',
                                                           effect_power=2),
            'stun': EffectsFactory.create_effect(effect_name='stun',
                                                 effect_power=0),
        }


class Rest(Action):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.action_name: str = 'rest'
        self.effects['gain_energy'] = EffectsFactory.create_effect(effect_name='gain_energy',
                                                                   effect_power=self.energy_cost)


class Pass(Action):
    def __init__(self, **kwargs):
        self.action_name: str = 'pass'
        super().__init__(**kwargs)


class ActionsFactory:
    action_classes: dict[str, type[Action]] = {
        'attack': Attack,
        'defence': Defence,
        'feint': Feint,
        'rest': Rest,
        'pass': Pass,
    }

    @classmethod
    def create_action(cls, action_name: str = '', **kwargs) -> Action:
        action_class = cls.action_classes.get(action_name)
        if action_class:
            return action_class(**kwargs)
        else:
            raise ValueError(f'Unknown action: {action_name}')


class Status:
    def __init__(self):
        self.status = {
            'health': 0,
            'energy': 0,
            'skip': False,
        }

    def __str__(self):
        return f'Heath: {self.status["health"]}, Energy: {self.status["energy"]}, Skip: {self.status["skip"]}'

    def apply_effect(self, effect: Effect):
        if effect.state == 'add':
            self.status[effect.parameter] += effect.effect_power

        elif effect.state == 'sub':
            self.status[effect.parameter] -= effect.effect_power

        elif effect.state == 'mul':
            self.status[effect.parameter] *= effect.effect_power

        elif effect.state == 'true':
            self.status[effect.parameter] = True
