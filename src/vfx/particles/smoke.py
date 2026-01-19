import pygame
import random

class SmokeParticle(pygame.sprite.Sprite):
    _CACHED_VARIANTS = []

    def __init__(self, pos, groups):
        super().__init__(groups)
        self.z_layer = 0 
        
        # Cache 5 variants of smoke to avoid runtime drawing
        if not SmokeParticle._CACHED_VARIANTS:
            for _ in range(5):
                size = random.randint(3, 7) # Tiny particles
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                col = random.randint(150, 180) # Darker smoke
                pygame.draw.circle(surf, (col, col, col, 50), (size//2, size//2), size//2) # Very faint alpha
                SmokeParticle._CACHED_VARIANTS.append(surf)
        
        self.image = random.choice(SmokeParticle._CACHED_VARIANTS).copy() 
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(random.uniform(-0.2, 0.2), random.uniform(-0.4, -0.1))
        self.alpha = 50
        self.fade_speed = random.uniform(400, 800) # Fade out quickly
        self.growth = random.uniform(1, 3)
        
    def update(self, dt):
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        # Performance optimization: Removed per-frame scaling
        # Just fade out
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.alpha))

class WalkParticle(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.z_layer = 0
        self.size = random.randint(10, 20)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        col = random.randint(140, 160)
        pygame.draw.circle(self.image, (col, col-10, col-20, 100), (self.size//2, self.size//2), self.size//2)
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.velocity = pygame.math.Vector2(random.uniform(-0.6, 0.6), random.uniform(-1.0, -0.3))
        self.alpha = 100
        self.fade_speed = random.uniform(300, 500)
        
    def update(self, dt):
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(max(0, min(255, self.alpha))))
