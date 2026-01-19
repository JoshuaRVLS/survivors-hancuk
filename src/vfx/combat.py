import pygame
import math
import random
from ..settings import *

class DeathEffect(pygame.sprite.Sprite):
    _CACHED_FRAMES = None

    def __init__(self, pos, groups):
        super().__init__(groups)
        self.z_layer = 1
        
        if DeathEffect._CACHED_FRAMES is None:
            DeathEffect._CACHED_FRAMES = []
            for i in range(8):
                size = 20 + i * 15 # Reduced size (was 40 + i*30)
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = 255 - (i * 32)
                center = size // 2
                radius = (size // 2) * (1.0 - i/8.0)
                if radius > 1:
                    pygame.draw.circle(surf, (255, 255, 255, alpha), (center, center), int(radius))
                pygame.draw.circle(surf, (200, 200, 200, alpha // 2), (center, center), size // 2, 4)
                
                # Simplified sparks for cached version (static pattern better for cache)
                for j in range(4):
                    ang = (j / 4) * 6.28 # Fixed angles for cache consistency
                    dist = size // 3
                    sp_x = center + int(math.cos(ang) * dist)
                    sp_y = center + int(math.sin(ang) * dist)
                    pygame.draw.circle(surf, (255, 255, 200, alpha), (sp_x, sp_y), 4)
                
                DeathEffect._CACHED_FRAMES.append(surf)

        self.frames = DeathEffect._CACHED_FRAMES
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        
    def update(self, dt):
        self.frame_index += 24 * dt
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            center = self.rect.center
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=center)

class SlashEffect(pygame.sprite.Sprite):
    _CACHED_FRAMES = {}

    def __init__(self, pos, groups, angle, player, scale=1.0, color=(0, 100, 255)):
        super().__init__(groups)
        self.player = player
        self.z_layer = 4 # Top layer
        
        # Smooth angle (Integer for cache)
        cache_key = (int(angle), round(scale, 2), color)
        
        if cache_key not in SlashEffect._CACHED_FRAMES:
            frames = []
            size = int(140 * scale)
            center = (size//2, size//2)
            
            # Helper to generate crescent polygon
            def generate_crescent(surf_size, arc_angle, thickness, fill_color, alpha):
                s = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                cx, cy = surf_size//2, surf_size//2
                
                points = []
                outer_rad = surf_size//2 - 10
                inner_rad = outer_rad - thickness
                
                # Outer Arc
                half_angle = arc_angle / 2
                steps = 15
                for i in range(steps + 1):
                    t = i / steps
                    a = math.radians(-half_angle + t * arc_angle)
                    points.append((cx + math.cos(a)*outer_rad, cy + math.sin(a)*outer_rad))
                
                # Inner Arc (Reverse)
                for i in range(steps, -1, -1):
                    t = i / steps
                    a = math.radians(-half_angle + t * arc_angle)
                    # Dynamic thickness taper at ends
                    taper = math.sin(t * 3.14159) # 0 at ends, 1 at center
                    r = outer_rad - (thickness * taper) 
                    points.append((cx + math.cos(a)*r, cy + math.sin(a)*r))
                    
                pygame.draw.polygon(s, (*fill_color, alpha), points)
                return s

            # --- FRAME GENERATION (Dynamic Color) ---
            # Frame 0: Start of swing (Narrow, short)
            f0 = generate_crescent(size, 60, 20, color, 200) 
            
            # Frame 1: Impact (Wide, Bright, White Core)
            # Make the 'bright' version slightly lighter if possible, or just same color with max alpha
            bright_color = tuple(min(255, c + 50) for c in color)
            f1 = generate_crescent(size, 140, 35, bright_color, 255)
            # Add white core
            f1_core = generate_crescent(size, 130, 15, (255, 255, 255), 255)
            f1.blit(f1_core, (0,0))
            
            # Frame 2: Follow through (Wide, Fading)
            f2 = generate_crescent(size, 140, 30, color, 150)
            
            # Frame 3: Dissipating (Thin, Transparent)
            f3 = generate_crescent(size, 140, 10, color, 50)

            raw_frames = [f0, f1, f2, f3]
            
            # Smooth rotation
            # Try positive angle if negative was incorrect
            rot_angle = -angle 
            
            for rf in raw_frames:
                frames.append(pygame.transform.rotate(rf, rot_angle))
                
            SlashEffect._CACHED_FRAMES[cache_key] = frames
            
        self.frames = SlashEffect._CACHED_FRAMES[cache_key]
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        self.pos_offset = pygame.math.Vector2(pos) - self.player.rect.center
        
        # Color for Shader (Neutral/White-Blue glow for sword)
        self.color = (color[0], color[1], color[2]) 
        
        # Shader Light Property
        self.radius = 60 # Sharper, cleaner flash
        
    def update(self, dt):
        self.frame_index += 15 * dt # Speed: ~0.25s total
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=self.rect.center)
            # Center offset logic remains, but we might want to drift it slightly forward?
            # For now keep attached
            self.rect.center = pygame.math.Vector2(self.player.rect.center) + self.pos_offset
