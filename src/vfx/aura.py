import pygame
import math
import random

class AuraParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, aura_radius):
        super().__init__(groups)
        self.z_layer = 1
        # Random position within radius
        angle = random.uniform(0, 360)
        dist = random.uniform(0, aura_radius)
        pos_offset = pygame.math.Vector2()
        pos_offset.from_polar((dist, angle))
            
        self.pos = pygame.math.Vector2(pos) + pos_offset
        self.velocity = pygame.math.Vector2(random.uniform(-0.3, 0.3), -random.uniform(0.5, 1.2))
        self.life = 1.0
        self.decay = random.uniform(0.015, 0.03)
        self.color = [255, 255, 180] # Pale Gold
        
        # Super small particles (1px radius = 2px size)
        size = 1
        self.image = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (*self.color, 255), (size, size), size)
        self.rect = self.image.get_rect(center=self.pos)

    def update(self, dt):
        self.life -= self.decay * dt * 60
        if self.life <= 0:
            self.kill()
            return
            
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # Fade out (Max alpha 180 for subtlety)
        alpha = int(180 * self.life)
        self.image.set_alpha(alpha)

class AuraSprite(pygame.sprite.Sprite):
    def __init__(self, groups, target, aura_radius, color=(255, 215, 0, 80)):
        self.z_layer = 0 # Draw below player
        super().__init__(groups)
        self.target = target
        self.aura_radius = aura_radius
        self.base_color = color
        
        # Layers Surfaces
        self.rune_surface = None
        self.ring_surface = None
        self.rune_angle = 0
        
        # Pre-calculate surface size based on diagonal of the bounding box
        # This prevents clipping or "big circles" appearing during rotation
        self._update_surf_size()
        
        self.pulse_time = 0
        self.particle_timer = 0
        self._init_layers()

    def _update_surf_size(self):
        # The diameter is radius * 2. The diagonal of a square is diameter * sqrt(2).
        # We use a 1.5 multiplier as a safe buffer.
        self.surf_size = int(self.aura_radius * 2 * 1.5)
        self.image = pygame.Surface((self.surf_size, self.surf_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=self.target.rect.center)

    def _init_layers(self):
        # Ring size is tighter to the radius
        ring_size = int(self.aura_radius * 2 + 10)
        center = ring_size // 2
        
        # 1. Rune Surface
        rune_r = self.aura_radius * 0.75
        self.rune_surface = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        
        points = []
        for i in range(6):
            angle = math.radians(i * 60)
            points.append((center + math.cos(angle) * rune_r, center + math.sin(angle) * rune_r))
        
        # Hexagon outline
        pygame.draw.polygon(self.rune_surface, (*self.base_color[:3], 100), points, 1)
        
        # Small rune dots at vertices
        for p in points:
            pygame.draw.circle(self.rune_surface, (255, 255, 255, 150), p, 2)
            pygame.draw.circle(self.rune_surface, self.base_color, p, 4, 1)

        # 2. Static Ring Surface
        self.ring_surface = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        # NO BACKGROUND FILL - Just outlines
        pygame.draw.circle(self.ring_surface, (*self.base_color[:3], 180), (center, center), self.aura_radius, 1)
        pygame.draw.circle(self.ring_surface, (*self.base_color[:3], 80), (center, center), self.aura_radius - 10, 1)

    def update(self, dt):
        if not self.target.alive():
            self.kill()
            return
            
        self.rect.center = self.target.rect.center
        
        # Animations
        self.pulse_time += dt * 3
        self.rune_angle += dt * 30 # Slow rotation
        
        # Particle Spawning (Subtle spawn rate)
        self.particle_timer += dt * 60
        if self.particle_timer > 15:
            self.particle_timer = 0
            AuraParticle(self.rect.center, self.groups(), self.aura_radius * 0.7)

        # Composite Rendering
        center = self.surf_size // 2
        self.image.fill((0, 0, 0, 0))
        
        # Alpha Pulse
        pulse = (math.sin(self.pulse_time) + 1) / 2 
        alpha = 100 + int(pulse * 80)
        
        # 1. Static Rings
        ring_rect = self.ring_surface.get_rect(center=(center, center))
        self.image.blit(self.ring_surface, ring_rect)
        
        # 2. Rotating Runes (Centered)
        rotated_runes = pygame.transform.rotate(self.rune_surface, self.rune_angle)
        rune_rect = rotated_runes.get_rect(center=(center, center))
        self.image.blit(rotated_runes, rune_rect)
        
        # 3. Inner Decorative Ring
        pygame.draw.circle(self.image, (255, 255, 255, 80), (center, center), int(self.aura_radius * 0.3), 1)
        
        self.image.set_alpha(alpha)
        
    def set_radius(self, new_radius):
        if int(new_radius) != int(self.aura_radius):
            self.aura_radius = new_radius
            self._update_surf_size()
            self._init_layers()
