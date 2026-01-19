import pygame

class HitSpark(pygame.sprite.Sprite):
    _CACHED_FRAMES = None

    def __init__(self, pos, groups):
        super().__init__(groups)
        self.z_layer = 3 
        
        if HitSpark._CACHED_FRAMES is None:
            HitSpark._CACHED_FRAMES = []
            for i in range(4):
                size = 30 + i * 15
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                alpha = 255 - (i * 60)
                center = size // 2
                pygame.draw.line(surf, (255, 255, 255, alpha), (0, center), (size, center), 3)
                pygame.draw.line(surf, (255, 255, 255, alpha), (center, 0), (center, size), 3)
                pygame.draw.circle(surf, (255, 255, 200, alpha), (center, center), size // 4)
                HitSpark._CACHED_FRAMES.append(surf)
                
        self.frames = HitSpark._CACHED_FRAMES
        self.frame_index = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        
    def update(self, dt):
        self.frame_index += 40 * dt
        if self.frame_index >= len(self.frames):
            self.kill()
        else:
            self.image = self.frames[int(self.frame_index)]
            self.rect = self.image.get_rect(center=self.rect.center) # Keep centered
