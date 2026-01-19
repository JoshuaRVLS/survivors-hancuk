import pygame
import math

class AuraSprite(pygame.sprite.Sprite):
    def __init__(self, groups, target, radius, color=(255, 215, 0, 50)):
        self._layer = 0 # Draw below player via LayeredUpdates
        super().__init__(groups)
        self.target = target
        self.radius = radius
        self.base_color = color
        
        # Create Surface
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=target.rect.center)
        self.pos = pygame.math.Vector2(self.rect.center)
        
        self.pulse_time = 0
        self._redraw()

    def _redraw(self):
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        # Outer Glow
        pygame.draw.circle(self.image, self.base_color, (self.radius, self.radius), self.radius)
        # Inner Ring
        pygame.draw.circle(self.image, (255, 255, 255, 100), (self.radius, self.radius), self.radius, 2)

    def update(self, dt):
        if not self.target.alive():
            self.kill()
            return
            
        # Follow Target
        self.rect.center = self.target.rect.center
        
        # Pulse Effect
        self.pulse_time += dt * 5
        pulse_scale = 1.0 + math.sin(self.pulse_time) * 0.05
        
        # We can't easily scale the image every frame without quality loss or lag.
        # Instead, maybe just alpha pulse?
        alpha = 100 + int(math.sin(self.pulse_time) * 40)
        self.image.set_alpha(alpha)
        
    def set_radius(self, new_radius):
        if int(new_radius) != int(self.radius):
            self.radius = new_radius
            self.image = pygame.Surface((int(new_radius) * 2, int(new_radius) * 2), pygame.SRCALPHA)
            self._redraw() # Recreate surface with new size
