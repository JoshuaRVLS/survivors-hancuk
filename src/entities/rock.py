import pygame
import os
from ..settings import TILE_SIZE

class Rock(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacles_group):
        super().__init__(groups)
        self.z_layer = 1 # Above floor
        
        # Load Rock and Shadow
        path = "assets/tiles/big_rock.png"
        shadow_path = "assets/tiles/big_rock_shadow.png"
        
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        # 1. Shadow
        if os.path.exists(shadow_path):
            shadow_surf = pygame.image.load(shadow_path).convert_alpha()
            self.image.blit(shadow_surf, (0, 0))
            
        # 2. Rock
        if os.path.exists(path):
            rock_surf = pygame.image.load(path).convert_alpha()
            self.image.blit(rock_surf, (0, 0))
        else:
            self.image.fill((100, 100, 100)) # Grey fallback
        self.rect = self.image.get_rect(topleft=pos)
        
        # Hitbox: Circular-ish base
        hitbox_size = 50
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.hitbox.center = self.rect.center
        self.hitbox.centery += 5 # Push down slightly
        
        if obstacles_group is not None:
            obstacles_group.add(self)
