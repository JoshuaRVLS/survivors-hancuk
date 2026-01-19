import pygame

class Interactable(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)
        self.pos = pygame.math.Vector2(pos)
        self.rect = None
        self.interaction_radius = 60
        self.z_layer = 1 # Same as entities usually
        
    def interact(self, player):
        pass
        
    def update(self, dt):
        pass
