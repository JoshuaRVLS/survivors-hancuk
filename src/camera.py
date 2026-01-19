import pygame
from .settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self, virtual_surface):
        super().__init__()
        self.virtual_surface = virtual_surface
        self.half_width = self.virtual_surface.get_size()[0] // 2
        self.half_height = self.virtual_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

    def resize(self, new_surface):
        self.virtual_surface = new_surface
        self.half_width = self.virtual_surface.get_size()[0] // 2
        self.half_height = self.virtual_surface.get_size()[1] // 2

    def update(self, dt):
        super().update(dt)
        if hasattr(self, 'target') and self.target:
            # Calculate Target Offset (Center Target)
            target_x = self.target.rect.centerx - self.half_width
            target_y = self.target.rect.centery - self.half_height
            
            # INITIAL SNAP: If offset is 0 (first frame), snap immediately to avoid "flying in"
            # Force Snap for now to fix off-center bug
            self.offset.x = target_x
            self.offset.y = target_y
            # if self.offset.magnitude() == 0:
            #    self.offset.x = target_x
            #    self.offset.y = target_y
            # else:
            #    # Smoothly move offset towards target (LERP) using dt
            #    self.offset.x += (target_x - self.offset.x) * 0.1 * dt * 60
            #    self.offset.y += (target_y - self.offset.y) * 0.1 * dt * 60

    def custom_draw(self):
        # FORCE UPDATE OFFSET HERE to Start Fix
        if hasattr(self, 'target') and self.target:
             target_x = self.target.rect.centerx - self.half_width
             target_y = self.target.rect.centery - self.half_height
             self.offset.x = target_x
             self.offset.y = target_y

        # Viewport rect for culling
        view_rect = pygame.Rect(self.offset.x, self.offset.y, self.virtual_surface.get_width(), self.virtual_surface.get_height())
        
        # 1. Cull & Sort
        # Only process sprites within or touching the camera view
        visible_sprites = [s for s in self.sprites() if view_rect.colliderect(s.rect)]
        
        sorted_sprites = sorted(
            visible_sprites, 
            key=lambda sprite: (getattr(sprite, 'z_layer', 0), sprite.rect.bottom)
        )
        
        # 2. Draw
        offset_vec = pygame.math.Vector2(int(self.offset.x), int(self.offset.y))
        
        # DEBUG: Print camera state once every 60 frames to avoid spam
        # import pygame

        for sprite in sorted_sprites:
            offset_pos = sprite.rect.topleft - offset_vec
            self.virtual_surface.blit(sprite.image, offset_pos)

            # Debug Drawing
            import __main__
            is_debug = getattr(__main__, 'game', None) and __main__.game.debug_mode
            if is_debug:
                # Draw Rect (Blue)
                pygame.draw.rect(self.virtual_surface, (0, 0, 255), (sprite.rect.topleft - offset_vec, sprite.rect.size), 1)
                # Draw Hitbox (Green)
                if hasattr(sprite, 'hitbox'):
                    pygame.draw.rect(self.virtual_surface, (0, 255, 0), (sprite.hitbox.topleft - offset_vec, sprite.hitbox.size), 2)
                # Draw Attack Hitbox (Red) if exists
                if hasattr(sprite, 'attack_hitbox') and sprite.attack_hitbox:
                    pygame.draw.rect(self.virtual_surface, (255, 0, 0), (sprite.attack_hitbox.topleft - offset_vec, sprite.attack_hitbox.size), 2)
