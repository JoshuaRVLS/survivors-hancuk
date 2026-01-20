import pygame
from .settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self, virtual_surface):
        super().__init__()
        self.virtual_surface = virtual_surface
        self.half_width = self.virtual_surface.get_size()[0] // 2
        self.half_height = self.virtual_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()
        
        # Asset Bayangan Universal
        import os
        shadow_path = "assets/Characters/Female/Shadow.png"
        if os.path.exists(shadow_path):
            self.universal_shadow = pygame.image.load(shadow_path).convert_alpha()
            # Perbesar bayangan (User request: radius terlalu kecil)
            orig_size = self.universal_shadow.get_size()
            new_size = (orig_size[0] * 3, orig_size[1] * 2) # Perlebar 3x, tinggi 2x
            self.universal_shadow = pygame.transform.scale(self.universal_shadow, new_size)
            # Buat sedikit lebih transparan agar tidak terlalu keras
            self.universal_shadow.set_alpha(160)
        else:
            self.universal_shadow = None

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
            
            # 3. Draw Universal Shadow for Characters
            # We identify characters by common attributes (health, status, etc.) 
            # or class names if imported (but we avoid circular imports)
            from .entities.player import Player
            from .entities.enemy import Enemy
            from .entities.remote_player import RemotePlayer
            
            if self.universal_shadow and isinstance(sprite, (Player, Enemy, RemotePlayer)):
                # Skip if it's already an Orc and has its own shadow? 
                # Actually, the user wants it for "every character".
                
                # Posisi bayangan: Tengah bawah hitbox
                sh_rect = self.universal_shadow.get_rect()
                
                # Gunakan hitbox jika ada, jika tidak rect
                char_hitbox = getattr(sprite, 'hitbox', sprite.rect)
                sh_rect.centerx = char_hitbox.centerx - offset_vec.x
                # Sesuaikan Y agar pas di bawah kaki (User report: ga pas, kurang atas)
                # char_hitbox.bottom adalah titik pijak, kita kurangi agar 'overlap' kaki
                sh_rect.centery = char_hitbox.bottom - offset_vec.y - 16 
                
                self.virtual_surface.blit(self.universal_shadow, sh_rect)

            self.virtual_surface.blit(sprite.image, offset_pos)

            # Debug Drawing
            import __main__
            is_debug = getattr(__main__, 'game', None) and __main__.game.debug_mode
            if is_debug:
                # Draw Rect (Blue)
                pygame.draw.rect(self.virtual_surface, (0, 0, 255), (sprite.rect.topleft - offset_vec, sprite.rect.size), 1)
                # Draw Hitbox (Yellow/Green)
                if hasattr(sprite, 'get_world_hitbox_points'):
                    points = sprite.get_world_hitbox_points()
                    screen_points = [(p[0] - offset_vec.x, p[1] - offset_vec.y) for p in points]
                    if len(screen_points) > 2:
                        pygame.draw.polygon(self.virtual_surface, (255, 255, 0), screen_points, 1)
                    for sp in screen_points:
                        pygame.draw.circle(self.virtual_surface, (255, 0, 0), sp, 2)
                elif hasattr(sprite, 'hitbox'):
                    pygame.draw.rect(self.virtual_surface, (0, 255, 0), (sprite.hitbox.topleft - offset_vec, sprite.hitbox.size), 2)
                # Draw Attack Hitbox (Red) if exists
                if hasattr(sprite, 'attack_hitbox') and sprite.attack_hitbox:
                    pygame.draw.rect(self.virtual_surface, (255, 0, 0), (sprite.attack_hitbox.topleft - offset_vec, sprite.attack_hitbox.size), 2)
            
            # Draw Mouse World Crosshair
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            # Simple crosshair at mouse screen pos
            pygame.draw.line(self.virtual_surface, (255, 0, 255), (mouse_pos.x - 10, mouse_pos.y), (mouse_pos.x + 10, mouse_pos.y), 1)
            pygame.draw.line(self.virtual_surface, (255, 0, 255), (mouse_pos.x, mouse_pos.y - 10), (mouse_pos.x, mouse_pos.y + 10), 1)
