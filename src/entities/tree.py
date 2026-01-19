import pygame
import os
import random
from ..settings import TILE_SIZE
from ..utils import load_sprite_sheet

class Tree(pygame.sprite.Sprite):
    def __init__(self, pos, groups, obstacles_group, variant='big'):
        super().__init__(groups)
        self.z_layer = 1 # Above floor
        self.variant = variant
        
        # Variant Configurations
        configs = {
            'big': {
                'path': 'assets/tiles/big_tree.png',
                'shadow_path': 'assets/tiles/big_tree_shadow.png',
                'size': (160, 160),
                'shadow_size': (128, 64),
                'hitbox': (60, 40),
                'hitbox_offset': -10
            },
            'medium': {
                'path': 'assets/tiles/medium_tree.png',
                'shadow_path': 'assets/tiles/medium_tree_shadow.png',
                'size': (96, 160),
                'shadow_size': (96, 64),
                'hitbox': (40, 30),
                'hitbox_offset': -8
            },
            'small': {
                'path': 'assets/tiles/small_tree.png',
                'shadow_path': 'assets/tiles/small_tree_shadow.png',
                'size': (96, 128),
                'shadow_size': (96, 64),
                'hitbox': (30, 25),
                'hitbox_offset': -5
            }
        }
        
        cfg = configs.get(variant, configs['big'])
        w, h = cfg['size']
        
        # Load Frames
        if os.path.exists(cfg['path']):
            raw_frames = load_sprite_sheet(cfg['path'], w, h)
        else:
            surf = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(surf, (34, 139, 34), (w//4, 0, w//2, h))
            raw_frames = [surf]

        # Load Shadow
        shadow_surf = None
        if os.path.exists(cfg['shadow_path']):
            shadow_surf = pygame.image.load(cfg['shadow_path']).convert_alpha()
        
        # Bake Shadows into Frames
        self.frames = []
        for frame in raw_frames:
            # We create a final surface to catch shadows if the frame is too small
            # (Though usually trees are tall enough)
            final_surf = frame.copy()
            if shadow_surf:
                # Center shadow at the bottom
                sh_w, sh_h = cfg['shadow_size']
                sh_x = (w - sh_w) // 2
                sh_y = h - sh_h
                final_surf.blit(shadow_surf, (sh_x, sh_y))
                # Blit the tree AGAIN on top of shadow to ensure trunk is over it
                final_surf.blit(frame, (0, 0))
            self.frames.append(final_surf)

        # Animation State
        self.frame_index = random.randint(0, len(self.frames) - 1) 
        self.animation_speed = random.uniform(1.5, 2.5) 
        
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(topleft=pos)
        
        # Hitbox
        hw, hh = cfg['hitbox']
        self.hitbox = pygame.Rect(0, 0, hw, hh)
        self.hitbox.midbottom = self.rect.midbottom
        self.hitbox.y += cfg['hitbox_offset']
        
        if obstacles_group is not None:
            obstacles_group.add(self)

    def animate(self, dt):
        if len(self.frames) > 1:
            self.frame_index += self.animation_speed * dt
            if self.frame_index >= len(self.frames):
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]

    def update(self, dt):
        self.animate(dt)
