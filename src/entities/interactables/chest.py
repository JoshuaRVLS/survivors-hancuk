import pygame
from ...utils import load_sprite_sheet
from .interactable import Interactable
from ...vfx.particles import LootParticle # Will need to update this import later

class Chest(Interactable):
    def __init__(self, pos, groups):
        super().__init__(pos, groups)
        
        if not groups:
            print("WARNING: Chest initialized with empty groups!")
        
        # Identify visual group for VFX
        self.vfx_group = None
        for g in groups:
            if hasattr(g, 'custom_draw'):
                self.vfx_group = g
                break
        
        # Load Assets
        try:
            full_sheet = load_sprite_sheet("assets/Animated Chests/Chests.png", 48, 32, scale=2.0)
        except Exception as e:
            print(f"ERROR Loading Chest Assets: {e}")
            full_sheet = None

        self.animations = {'idle': [], 'open': []}
        
        print(f"Spawned Chest at {pos}")
        
        if full_sheet and len(full_sheet) >= 10:
            self.animations['idle'] = full_sheet[0:5]
            self.animations['open'] = full_sheet[5:10]
        else:
            # Fallback
            s = pygame.Surface((48*2, 32*2))
            s.fill((139, 69, 19))
            self.animations['idle'] = [s]
            self.animations['open'] = [s]
            
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        
        # Physics / Rendering properties
        self.hitbox = self.rect.copy()
        self.hitbox.height = 20
        self.hitbox.bottom = self.rect.bottom
        
        self.state = 'closed'
        self.frame_index = 0
        self.animation_speed = 0.10 # Slightly slower for idle
        self.opened = False
        
    def interact(self, player):
        if self.state == 'closed':
            self.state = 'opening'
            self.frame_index = 0
            
    def update(self, dt):
        if self.state == 'closed':
            # Play Idle Animation (Loop)
            self.frame_index += self.animation_speed * dt * 60
            if self.frame_index >= len(self.animations['idle']):
                self.frame_index = 0
            self.image = self.animations['idle'][int(self.frame_index)]
            
        elif self.state == 'opening':
            # Play Open Animation (Once)
            self.frame_index += 0.15 * dt * 60 # Faster opening
            if self.frame_index >= len(self.animations['open']):
                self.frame_index = len(self.animations['open']) - 1
                self.state = 'open'
                self.opened = True
                print("Chest Opened!")
                
                # Spawn Loot Particles
                if hasattr(self, 'vfx_group') and self.vfx_group:
                    for _ in range(15):
                        LootParticle(self.rect.center, [self.vfx_group])
            
            self.image = self.animations['open'][int(self.frame_index)]
