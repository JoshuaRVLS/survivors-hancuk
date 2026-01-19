import pygame
from ..settings import *
from ..utils import load_sprite_sheet

class RemotePlayer(pygame.sprite.Sprite):
    def __init__(self, pid, groups, char_type='adventurer'):
        super().__init__(groups)
        self.pid = pid
        self.char_type = char_type
        self.z_layer = 5 # Same as player
        
        # Load Assets (Simplified - we assume we have access to similar asset loading as Player)
        # Ideally, we refactor Player's asset loading to be static/shared, but for now we duplicate or use a helper
        self.import_assets()
        
        self.status = 'idle_down'
        self.frame_index = 0
        self.image = self.animations[self.status][0]
        self.rect = self.image.get_rect()
        
        # Interpolation
        self.target_pos = pygame.math.Vector2()
        self.pos = pygame.math.Vector2()
        
    def import_assets(self):
        # Quick asset loader reuse
        # This duplicates Player logic slightly but is safer for now
        data = CHARACTER_DATA.get(self.char_type, CHARACTER_DATA['adventurer'])
        base_path = data['asset_path']
        scale = 2.5
        
        self.animations = {}
        
        # Simplified loading given we don't have all Player complex logic context easily available without refactoring
        # We will load basic movements
        dirs = ['down', 'up', 'left', 'right']
        
        # Check if female or adventurer
        is_female = 'female' in data['name'].lower()
        width, height = data.get('frame_size', (48, 64)) if is_female else (96, 80)
        
        if is_female:
            # Female Mapping
            # (Idle, Walk, Dash, Death)
            dirs_map = {'Down': 'down', 'Up': 'up', 'Left_Down': 'left', 'Right_Down': 'right'}
            anim_folders = [('Idle', 'idle'), ('Walk', 'run'), ('Dash', 'dash')]
            
            import os
            for folder, key in anim_folders:
                 for f_suffix, status_dir in dirs_map.items():
                    # Patterns...
                    patterns = [f"{folder}_{f_suffix}.png", f"{folder.lower()}_{f_suffix}.png"]
                    path = None
                    for p in patterns:
                        t = os.path.join(base_path, folder, p)
                        if os.path.exists(t): path = t; break
                    
                    if path:
                        frames = load_sprite_sheet(path, width, height, scale=scale, trim=True)
                        if frames: self.animations[f'{key}_{status_dir}'] = frames
                        
            # Fill missing
            for d in dirs:
                 if f'idle_{d}' not in self.animations: self.animations[f'idle_{d}'] = []
                 if f'run_{d}' not in self.animations: self.animations[f'run_{d}'] = self.animations[f'idle_{d}']

        else:
            # Adventurer Mapping
            import os
            for d in dirs:
                self.animations[f'idle_{d}'] = load_sprite_sheet(os.path.join(base_path, "IDLE", f"idle_{d}.png"), 96, 80, scale=scale, trim=True)
                self.animations[f'run_{d}'] = load_sprite_sheet(os.path.join(base_path, "RUN", f"run_{d}.png"), 96, 80, scale=scale, trim=True)

    def update_state(self, pos, status, char_type=None):
        self.target_pos = pygame.math.Vector2(pos)
        self.status = status
        
        # Check Character Switch
        if char_type and char_type != self.char_type:
             self.char_type = char_type
             self.import_assets()
             # Reset frame
             self.frame_index = 0
             if self.status in self.animations:
                 self.image = self.animations[self.status][0]

    def update(self, dt):
        # Interpolate Position
        if self.pos.distance_to(self.target_pos) > 200:
            # Snap if too far (teleport)
            self.pos = self.target_pos.copy()
        else:
             # Smooth LERP
             self.pos += (self.target_pos - self.pos) * 10 * dt
        
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # Animation
        if self.status in self.animations:
            self.frame_index += 0.15 # Use constant speed for remote players
            if self.frame_index >= len(self.animations[self.status]):
                self.frame_index = 0
            self.image = self.animations[self.status][int(self.frame_index)]

    def perform_attack(self, weapon_id, angles):
        # Visual Spawning Only
        import math
        
        # Filter groups: We do NOT want to add VFX to the 'remote_players' group
        # incorrectly. We just want 'camera_group' (usually index 0 or found by type)
        vfx_groups = []
        for g in self.groups():
             # Basic heuristic: if it has 'custom_draw', it's camera.
             # If it's the remote_players group, skip it.
             # We can just check hasattr(g, 'custom_draw')
             if hasattr(g, 'custom_draw'):
                 vfx_groups.append(g)
        
        # Fallback if empty (shouldn't happen if remote player is rendered)
        if not vfx_groups: vfx_groups = self.groups()

        # 1. Fireball
        if weapon_id == 'fireball':
            from ..vfx import Fireball
            for angle in angles:
                 rad = math.radians(angle)
                 dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                 Fireball(self.rect.center, vfx_groups, dir_vec, self, [], [], damage=0)
            return

        # 2. Slash
        from ..vfx import SlashEffect
        w_data = WEAPON_DATA.get(weapon_id, WEAPON_DATA['sword'])
        scale = w_data.get('range', 100) / 120.0
        color = w_data.get('slash_color', (255, 255, 255))
        
        for angle in angles:
             SlashEffect(self.rect.center, vfx_groups, angle, self, scale=scale, color=color)
