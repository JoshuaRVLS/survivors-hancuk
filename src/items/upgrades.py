
UPGRADE_DATA = {
    'damage_up': {
        'name': 'Might',
        'description': 'Increases damage by 20%.',
        'target': 'weapon',
        'stat': 'damage',
        'value': 1.2,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/damage_up.png'
    },
    'cooldown_down': {
        'name': 'Haste',
        'description': 'Reduces attack cooldown by 15%.',
        'target': 'weapon',
        'stat': 'cooldown',
        'value': 0.85,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/cooldown_down.png'
    },
    'range_up': {
        'name': 'Reach',
        'description': 'Increases attack range by 25.',
        'target': 'weapon',
        'stat': 'range',
        'value': 25,
        'op': 'add',
        'icon_path': 'assets/Upgrades/range_up.png'
    },
    'multishot': {
        'name': 'Duplicator',
        'description': 'Adds +1 Base Projectile.',
        'target': 'weapon',
        'stat': 'projectile_count',
        'value': 1,
        'op': 'add',
        'icon_path': 'assets/Upgrades/multishot.png'
    },
    'speed_up': {
        'name': 'Wings',
        'description': 'Increases movement speed by 10%.',
        'target': 'player',
        'stat': 'speed',
        'value': 1.1,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/speed_up.png'
    },
    'health_up': {
        'name': 'Hollow Heart',
        'description': 'Increases Max Health by 20.',
        'target': 'player',
        'stat': 'max_health',
        'value': 20,
        'op': 'add_heal', # Special op: add max and heal amount
        'icon_path': 'assets/Upgrades/health_up.png'
    },
    'stamina_up': {
        'name': 'Energy Drink',
        'description': 'Increases Stamina Regen by 20%.',
        'target': 'player',
        'stat': 'stamina_regen',
        'value': 1.2,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/stamina_up.png'
    },
    'unlock_aura': {
        'name': 'Holy Aura',
        'description': 'Unlocks a damaging aura around you.',
        'target': 'player',
        'stat': None,
        'value': 'aura',
        'op': 'unlock',
        'icon_path': 'assets/Upgrades/unlock_aura.png',
        'req_missing': 'aura' # Only show if player doesn't have 'aura'
    },
    'aura_radius': {
        'name': 'Expand Aura',
        'description': 'Increases Aura Radius by 20%.',
        'target': 'weapon.aura',
        'stat': 'range',
        'value': 1.2,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/aura_radius.png',
        'req_weapon': 'aura' # Only show if player HAS 'aura'
    },
    'aura_damage': {
        'name': 'Holy Burn',
        'description': 'Increases Aura Damage by 20%.',
        'target': 'weapon.aura',
        'stat': 'damage',
        'value': 1.2,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/aura_damage.png',
        'req_weapon': 'aura' 
    },
    'unlock_fireball': {
        'name': 'Fireball',
        'description': 'Unlocks a fireball projectile.',
        'target': 'player',
        'stat': None,
        'value': 'fireball',
        'op': 'unlock',
        'icon_path': 'assets/Upgrades/unlock_fireball.png',
        'req_missing': 'fireball'
    },
    'fireball_damage': {
        'name': 'Pyromancy',
        'description': '+20% Fireball Damage',
        'target': 'weapon.fireball',
        'stat': 'damage',
        'value': 1.2,
        'op': 'mult',
        'icon_path': 'assets/Upgrades/fireball_damage.png',
        'req_weapon': 'fireball'
    },
    'fireball_multishot': {
        'name': 'Dual Cast',
        'description': '+1 Fireball Projectile',
        'target': 'weapon.fireball',
        'stat': 'projectile_count',
        'value': 1,
        'op': 'add',
        'icon_path': 'assets/Upgrades/fireball_multishot.png',
        'req_weapon': 'fireball' 
    }
}
