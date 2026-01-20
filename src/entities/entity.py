
import pygame
from ..settings import *
from ..utils import load_sprite_sheet
from ..core.collision import SAT
import json
import os

class Entity(pygame.sprite.Sprite):
    def __init__(self, pos, groups, z_layer=1):
        super().__init__(groups)
        self.z_layer = z_layer
        self.status = 'idle'
        self.frame_index = 0
        self.animations = {}
        
        # Physics
        self.direction = pygame.math.Vector2()
        self.pos = pygame.math.Vector2(pos)
        self.knockback_vector = pygame.math.Vector2()
        
        # State
        self.is_dead = False
        self.is_hurting = False
        self.hurt_time = 0
        self.hitbox_offset_y = 0 # Offset for 2.5D alignment
        
        # Custom Hitbox Data (Vertex Points)
        self.custom_hitbox = None 
        self._load_custom_hitbox()
        
    def _sync_hitbox_with_pos(self):
        self.hitbox.centerx = self.pos.x + self.rect.width/2
        self.hitbox.centery = self.pos.y + (self.rect.height / 2 + self.hitbox_offset_y)

    def _sync_pos_with_hitbox(self):
        self.pos.x = self.hitbox.centerx - self.rect.width/2
        self.pos.y = self.hitbox.centery - (self.rect.height / 2 + self.hitbox_offset_y)
        
    def _load_custom_hitbox(self):
        # Cari data berdasarkan nama class atau config
        entity_id = getattr(self, 'enemy_type', None) or getattr(self, 'char_config', {}).get('name', '').lower()
        if not entity_id: return
        
        path = "assets/data/collisions.json"
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    
                    # Match exact or prefix (e.g., orc_captain matches orc)
                    found_key = None
                    if entity_id in data:
                        found_key = entity_id
                    else:
                        # Try prefix matching for variants
                        for key in data.keys():
                            if entity_id.startswith(key):
                                found_key = key
                                break
                    
                    if found_key:
                        self.custom_hitbox = data[found_key]["points"]
                        self.hitbox_ref_size = data[found_key].get("ref_size")
            except:
                pass

    def get_world_hitbox_points(self):
        if not self.custom_hitbox:
            # Fallback to rect points
            return [self.hitbox.topleft, self.hitbox.topright, self.hitbox.bottomright, self.hitbox.bottomleft]
        
        # Scale logic
        scale_x = self.rect.width / self.hitbox_ref_size[0] if self.hitbox_ref_size else 1.0
        scale_y = self.rect.height / self.hitbox_ref_size[1] if self.hitbox_ref_size else 1.0
        
        # Konversi poin relatif editor ke koordinat dunia (berdasarkan rect)
        return [(p[0] * scale_x + self.rect.x, p[1] * scale_y + self.rect.y) for p in self.custom_hitbox]
    def animate(self, dt):
        # Handle status logic in subclasses
        animation_speed = ANIMATION_SPEED if not self.status.startswith('attack') else ATTACK_ANIMATION_SPEED
        
        # Check if animation group exists
        if self.status not in self.animations or not self.animations[self.status]:
            return
            
        self.frame_index += animation_speed * dt * 60
        if self.frame_index >= len(self.animations[self.status]):
            if self.status.startswith('attack') or self.status.startswith('hurt'):
                # Reset to idle
                if self.status.startswith('hurt'):
                    self.is_hurting = False
                self.status = 'idle'
                self.frame_index = 0
            elif self.status.startswith('death'):
                self.frame_index = len(self.animations[self.status]) - 1
            else:
                self.frame_index = 0
                
        # Final safety check before indexing
        if self.status in self.animations and self.animations[self.status]:
            self.image = self.animations[self.status][int(self.frame_index)]
        else:
            # Fallback for directional entities where 'idle' is not a key
            # Subclasses like Player will fix this in their next update() call
            pass
        # We don't set rect.topleft here; subclasses should sync rect with self.pos

    def _apply_velocity_with_collision(self, velocity, obstacle_sprites, enemy_sprites=None):
        # Step velocity logic to prevent phasing
        step_dist = 16
        magnitude = velocity.magnitude()
        
        if magnitude > 0:
            num_steps = int(magnitude / step_dist) + 1
            step_vel = velocity / num_steps
            
            for _ in range(num_steps):
                # 1. Horizontal
                self.pos.x += step_vel.x
                self._sync_hitbox_with_pos()
                self.collision('horizontal', step_vel.x, obstacle_sprites, enemy_sprites)
                
                # 2. Vertical
                self.pos.y += step_vel.y
                self._sync_hitbox_with_pos()
                self.collision('vertical', step_vel.y, obstacle_sprites, enemy_sprites)

        # Sync visual rect
        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom

    def collision(self, direction, vel, obstacle_sprites, enemy_sprites=None):
        # Subclasses should implement specific collision targets
        pass

    def apply_knockback(self, dt):
        if self.knockback_vector.magnitude() > 0.1:
            self._apply_velocity_with_collision(self.knockback_vector * dt * 60, getattr(self, 'obstacle_sprites', None))
            # Smooth decay (Softened for better feel)
            self.knockback_vector *= pow(0.85, dt * 60)
        else:
            self.knockback_vector = pygame.math.Vector2()
            self._sync_hitbox_with_pos() # Final cleanup
