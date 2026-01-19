import pygame
import random

class LootParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.z_layer = 4 # Above most things
        
        size = random.randint(4, 7)
        self.image = pygame.Surface((size, size))
        # Gold/Yellow variations
        c = random.randint(200, 255)
        self.image.fill((c, 215, 0))
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        
        # Burst upwards
        self.velocity = pygame.math.Vector2(random.uniform(-2, 2), random.uniform(-4, -1))
        self.alpha = 255
        self.fade_speed = random.uniform(200, 400)
        self.gravity = 0.1
        
    def update(self, dt):
        self.velocity.y += self.gravity * dt * 60
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.alpha))
