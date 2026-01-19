import pygame

class GhostSprite(pygame.sprite.Sprite):
    def __init__(self, pos, image, groups):
        super().__init__(groups)
        self.image = image.copy()
        self.rect = self.image.get_rect(topleft=pos)
        self.alpha = 200
        self.decay_rate = 300 
        self.z_layer = 1
        
    def update(self, dt):
        self.alpha -= self.decay_rate * dt
        if self.alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(int(self.alpha))
