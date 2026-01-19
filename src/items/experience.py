import pygame
import random

class ExperienceGem(pygame.sprite.Sprite):
    _CACHED_IAMGE = None

    def __init__(self, pos, groups, player):
        super().__init__(groups)
        self.player = player
        self.z_layer = 0
        self.size = 12
        
        if ExperienceGem._CACHED_IAMGE is None:
            surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.circle(surf, (0, 255, 200, 200), (self.size//2, self.size//2), self.size//2)
            pygame.draw.circle(surf, (255, 255, 255, 255), (self.size//2, self.size//2), self.size//4)
            ExperienceGem._CACHED_IAMGE = surf
            
        self.image = ExperienceGem._CACHED_IAMGE
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-2, 2))
        self.acceleration = 1.2
        self.magnet_range = 400
        self.pickup_range = 30

    def update(self, dt):
        player_center = pygame.math.Vector2(self.player.rect.center)
        direction = player_center - self.pos
        distance = direction.magnitude()
        if distance < self.magnet_range:
            if distance > 0:
                direction = direction.normalize()
                
                # Super Homing (No orbit)
                if distance < 60:
                    self.velocity = direction * 25 # Snap to player
                else:
                    self.velocity += direction * self.acceleration * dt * 60
                    if self.velocity.magnitude() > 15:
                        self.velocity = self.velocity.normalize() * 15
        else:
            self.velocity *= pow(0.98, dt * 60)
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if distance < self.pickup_range:
            self.player.gain_exp(10)
            self.kill()
