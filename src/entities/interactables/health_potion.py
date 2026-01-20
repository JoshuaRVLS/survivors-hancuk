import pygame
import random
import os
from .interactable import Interactable

class HealthPotion(Interactable):
    def __init__(self, pos, groups, player):
        super().__init__(pos, groups)
        self.player = player
        self.z_layer = 1 # Above shadows
        
        # Load Animation Assets
        self.frames = []
        asset_dir = "assets/tiles/HealthPotion"
        if os.path.exists(asset_dir):
            # Sort files to ensure correct animation order
            try:
                files = sorted([f for f in os.listdir(asset_dir) if f.endswith(".png")])
                for f in files:
                    img = pygame.image.load(os.path.join(asset_dir, f)).convert_alpha()
                    # Rescale to user-specified size: 22x37
                    img = pygame.transform.scale(img, (22, 37))
                    self.frames.append(img)
            except Exception as e:
                print(f"Error loading potion animation: {e}")
        
        if not self.frames:
            # Fallback
            s = pygame.Surface((22, 37))
            s.fill((255, 0, 0))
            self.frames = [s]
            
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.frame_index = 0
        self.animation_speed = 0.15
        
        # Drop Physics (The "Pop" effect)
        angle = random.uniform(0, 360)
        dist = random.uniform(2, 5)
        self.velocity = pygame.math.Vector2()
        self.velocity.from_polar((dist, angle))
        
        self.z_height = 0  # Visual altitude
        self.z_velocity = -random.uniform(5, 8) # Initial pop up (Negative is UP in this context)
        self.gravity = 0.4
        self.bounce_factor = 0.5
        
        self.collecting = False
        self.pull_range = 100
        self.pickup_range = 20
        self.heal_amount = 25
        
    def update(self, dt):
        # 1. Animation
        self.frame_index += self.animation_speed * dt * 60
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]
        
        # 2. Collection Logic
        player_center = pygame.math.Vector2(self.player.rect.center)
        direction = player_center - self.pos
        distance = direction.magnitude()

        if not self.collecting:
            if distance < self.pull_range:
                self.collecting = True
        
        if self.collecting:
            # Gravitate strongly
            if distance > 0:
                direction = direction.normalize()
                # Rapidly accelerate towards player
                pull_speed = 25
                self.velocity = direction * pull_speed
                # Move towards ground Z as we are collected
                self.z_height *= 0.9
        else:
            # Normal Physics (Pop and Friction)
            self.velocity *= pow(0.92, dt * 60)
            
            # Vertical movement (Z)
            if self.z_velocity != 0 or self.z_height < 0:
                self.z_velocity += self.gravity * dt * 60
                self.z_height += self.z_velocity * dt * 60
                
                # Ground collision (Bounce)
                if self.z_height >= 0:
                    self.z_height = 0
                    if abs(self.z_velocity) > 1:
                        self.z_velocity = -self.z_velocity * self.bounce_factor
                    else:
                        self.z_velocity = 0

        # Apply visual position
        self.pos += self.velocity * dt * 60
        self.rect.centerx = round(self.pos.x)
        self.rect.centery = round(self.pos.y + self.z_height)
        
        # Actual Pickup
        if distance < self.pickup_range:
            self.apply_pickup()

    def apply_pickup(self):
        if hasattr(self.player, 'health') and hasattr(self.player, 'max_health'):
            self.player.health = min(self.player.max_health, self.player.health + self.heal_amount)
        self.kill()
