import pygame
import math
import random
from ..settings import *
from .particles import SmokeParticle

class Fireball(pygame.sprite.Sprite):
    def __init__(self, pos, groups, direction_vec, player, obstacle_sprites, enemy_sprites, damage=None, speed=None):
        super().__init__(groups)
        self.player = player
        self.obstacle_sprites = obstacle_sprites
        self.enemy_sprites = enemy_sprites
        self.z_layer = 2
        
        self.size = 24
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 50, 0, 230), (self.size//2, self.size//2), self.size//2) # Red/Orange
        pygame.draw.circle(self.image, (255, 200, 50, 255), (self.size//2, self.size//2), self.size//4) # Yellow Core
        self.rect = self.image.get_rect(center=pos)
        
        self.pos = pygame.math.Vector2(self.rect.center)
        self.direction = direction_vec.normalize() if direction_vec.magnitude() > 0 else pygame.math.Vector2(1,0)
        self.speed = speed if speed is not None else 12
        self.damage = damage if damage is not None else player.damage * 1.5
        self.radius = 120 # Shader light radius
        self.color = (255, 80, 20) # Fire Orange
        self.light_radius = 0.08 # Barely visible glow (legacy)
        
        # Life safety
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 2000 # 2 seconds max life
        
    def update(self, dt):
        self.pos += self.direction * self.speed * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # Kill if too old
        if pygame.time.get_ticks() - self.spawn_time > self.lifetime:
            self.kill()
            return

        # Custom collision check for obstacles (using hitboxes)
        # Custom collision check for obstacles (using hitboxes)
        # 1. Obstacles - OPTIMIZED
        # Use spritecollide to get candidate obstacles (C-optimized AABB check)
        # This prevents iterating 4000+ trees in Python
        candidate_obstacles = pygame.sprite.spritecollide(self, self.obstacle_sprites, False)
        
        for obstacle in candidate_obstacles:
            target_hit = getattr(obstacle, 'hitbox', obstacle.rect)
            if self.rect.colliderect(target_hit):
                self.explode()
                return
            
        # 2. Enemies
        hit_enemies = pygame.sprite.spritecollide(self, self.enemy_sprites, False, pygame.sprite.collide_rect)
        for enemy in hit_enemies:
            if hasattr(enemy, 'is_dead') and not enemy.is_dead and hasattr(enemy, 'hitbox'):
                # Finer check with hitbox
                if enemy.hitbox.colliderect(self.rect):
                    enemy.health -= self.damage
                    enemy.is_hurting = True
                    enemy.hurt_time = pygame.time.get_ticks()
                    kb_dir = (enemy.pos - self.pos).normalize() if (enemy.pos - self.pos).magnitude() > 0 else self.direction
                    enemy.knockback_vector = kb_dir * 40
                    
                    if hasattr(self.player, 'game'):
                        self.player.game.is_hit_stopped = True
                        self.player.game.hit_stop_timer = pygame.time.get_ticks()
                    
                    self.explode()
                    return

    def explode(self):
        FireBlast(self.rect.center, self.groups())
        self.kill()


class FireBlast(pygame.sprite.Sprite):
    # Class-level cache to prevent laggy surface creation
    _CACHED_FRAMES = None

    def __init__(self, pos, groups):
        super().__init__(groups)
        self.z_layer = 4
        
        if FireBlast._CACHED_FRAMES is None:
            FireBlast._CACHED_FRAMES = []
            for i in range(8): # Reduced frames for speed
                size = 30 + i * 10 # Reduced size (was 60 + i*15/20)
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = 255 - (i * 30)
                color = (255, 100 - i * 10, 0, alpha) # Darker orange, less blinding
                pygame.draw.circle(surf, color, (size//2, size//2), size//2)
                pygame.draw.circle(surf, (255, 200, 100, alpha), (size//2, size//2), size//4)
                FireBlast._CACHED_FRAMES.append(surf)
                
        self.frames = FireBlast._CACHED_FRAMES
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center) # Ensure pos exists for main.py
        self.color = (255, 120, 20) # Fire Orange
        self.light_intensity = 0.8 # Reduced light intensity base

    def update(self, dt):
        self.frame_index += 30 * dt
        self.light_intensity = 1.0 - (self.frame_index / len(self.frames))
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            center = self.rect.center
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=center)
