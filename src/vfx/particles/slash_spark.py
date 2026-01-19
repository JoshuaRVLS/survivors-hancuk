import pygame
import random

class SlashSpark(pygame.sprite.Sprite):
    def __init__(self, pos, groups, direction_vec, base_color=(0, 255, 255)):
        super().__init__(groups)
        self.z_layer = 3
        
        size = random.randint(2, 4) # Smaller sparks
        self.image = pygame.Surface((size, size))
        
        # Variate color slightly based on base_color
        # Simple variation: slightly whiter or darker
        c = base_color
        variants = [
            c,
            (min(255, c[0]+50), min(255, c[1]+50), min(255, c[2]+50)),
            (max(0, c[0]-30), max(0, c[1]-30), max(0, c[2]-30))
        ]
        color = random.choice(variants)
        self.image.fill(color)
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.center)
        
        # Velocity based on slash direction + random spread
        spread = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
        self.velocity = direction_vec * random.uniform(2, 5) + spread
        self.alpha = 255
        self.fade_speed = random.uniform(400, 800)
        
    def update(self, dt):
        self.pos += self.velocity * dt * 60
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.alpha))
