import pygame
import os
import random
from .settings import *
from .utils import load_sprite_sheet

class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, image, groups, z_layer=-1):
        super().__init__(groups)
        self.image = image
        self.rect = self.image.get_rect(topleft=pos)
        self.z_layer = z_layer

class ChunkManager:
    def __init__(self, camera_group, obstacles_group=None):
        self.camera_group = camera_group
        self.obstacles_group = obstacles_group
        self.tile_size = TILE_SIZE
        self.chunk_size = CHUNK_SIZE # Tiles per side
        self.chunk_pixel_size = self.chunk_size * self.tile_size
        
        # Loaded chunks: {(cx, cy): [sprite1, sprite2, ...]}
        self.active_chunks = {}
        
        # Load Tilesets (Auto-scaled to TILE_SIZE)
        self.grass_tiles = self._load_tiles("assets/tiles/grass.png")
        self.flower_tiles = self._load_tiles("assets/tiles/grass_with_flower.png")
        self.paving_tiles = self._load_tiles("assets/tiles/paving_stones.png")
        # rocks.png is 192x32, so 6 tiles of 32x32
        self.rock_tiles = self._load_tiles("assets/tiles/rocks.png")
        self.rock_shadows = self._load_tiles("assets/tiles/rocks_shadow.png")
        
        if not self.grass_tiles:
            self.grass_tiles = [pygame.Surface((self.tile_size, self.tile_size))]
            self.grass_tiles[0].fill((34, 139, 34))

    def _load_tiles(self, path):
        if not os.path.exists(path):
            print(f"Warning: Tileset not found at {path}")
            return []
            
        # Assets are 32x32, we scale to TILE_SIZE (usually 64)
        source_size = 32
        return load_sprite_sheet(path, source_size, source_size, scale=self.tile_size/source_size)

    def get_chunk_coord(self, pos):
        cx = int(pos[0] // self.chunk_pixel_size)
        cy = int(pos[1] // self.chunk_pixel_size)
        return cx, cy

    def update(self, player_pos):
        p_cx, p_cy = self.get_chunk_coord(player_pos)
        
        # Target coords in radius
        target_chunks = set()
        for dx in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
            for dy in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
                target_chunks.add((p_cx + dx, p_cy + dy))
        
        # Unload far chunks
        current_chunks = list(self.active_chunks.keys())
        for coord in current_chunks:
            if coord not in target_chunks:
                self.unload_chunk(coord)
        
        # Load new chunks
        for coord in target_chunks:
            if coord not in self.active_chunks:
                self.load_chunk(coord)

    def load_chunk(self, coord):
        cx, cy = coord
        sprites = []
        
        # 1. Baked Floor Rendering
        # Create a single surface for the entire chunk's floor
        baked_surface = pygame.Surface((self.chunk_pixel_size, self.chunk_pixel_size), pygame.SRCALPHA)
        
        for ty in range(self.chunk_size):
            for tx in range(self.chunk_size):
                gx = cx * self.chunk_size + tx
                gy = cy * self.chunk_size + ty
                rng = random.Random(f"tile_{gx}_{gy}")
                
                # Render logic (Draw directly to baked_surface)
                base_image = rng.choice(self.grass_tiles)
                decor_image = None
                decor_shadow = None
                
                # Small Rocks
                if self.rock_tiles and rng.random() < 0.03:
                    rock_idx = rng.randint(0, len(self.rock_tiles) - 1)
                    decor_image = self.rock_tiles[rock_idx]
                    if self.rock_shadows and rock_idx < len(self.rock_shadows):
                        decor_shadow = self.rock_shadows[rock_idx]
                # Paving Stones
                elif self.paving_tiles and rng.random() < 0.02:
                    decor_image = rng.choice(self.paving_tiles)
                # Flower Clustering
                elif not decor_image:
                    cluster_scale = 6
                    patch_rng = random.Random(f"patch_{gx//cluster_scale}_{gy//cluster_scale}")
                    if patch_rng.random() < 0.12 and self.flower_tiles:
                        if rng.random() < 0.35:
                            decor_image = rng.choice(self.flower_tiles)
                
                # Draw to baked surface
                dest_pos = (tx * self.tile_size, ty * self.tile_size)
                baked_surface.blit(base_image, dest_pos)
                if decor_shadow:
                    baked_surface.blit(decor_shadow, dest_pos)
                if decor_image:
                    baked_surface.blit(decor_image, dest_pos)

        # Create ONE sprite for the whole floor chunk
        world_x = cx * self.chunk_pixel_size
        world_y = cy * self.chunk_pixel_size
        floor_sprite = Tile((world_x, world_y), baked_surface, [self.camera_group], z_layer=-1)
        sprites.append(floor_sprite)

        # 2. Entity Spawning (Separate from baked floor for depth sorting)
        for ty in range(self.chunk_size):
            for tx in range(self.chunk_size):
                gx = cx * self.chunk_size + tx
                gy = cy * self.chunk_size + ty
                
                # BIOME LOGIC: Check macro region for forest density
                biome_scale = 32 # Macro-scale biomes
                biome_rng = random.Random(f"biome_{gx//biome_scale}_{gy//biome_scale}")
                is_forest = biome_rng.random() < 0.35 
                
                # Local RNG for the specific tile/entity slot
                rng = random.Random(f"ent_{gx}_{gy}") 
                rand_val = rng.random()
                
                # Jitter for organic placement (+/- 15px)
                jitter_x = rng.randint(-15, 15)
                jitter_y = rng.randint(-15, 15)
                
                # Determine Spawn Probabilities on 1x1 Grid
                if is_forest:
                    tree_target = 0.22 # Dense enough to cluster but not a solid wall
                    rock_target = 0.25 # Total 3% rocks
                else:
                    tree_target = 0.012 # 1.2% sparse trees
                    rock_target = 0.03 # 1.8% sparse rocks
                
                world_x = gx * self.tile_size + jitter_x
                world_y = gy * self.tile_size + jitter_y
                
                # 1. Trees
                if rand_val < tree_target:
                    from .entities.tree import Tree
                    v_rand = rng.random()
                    if v_rand < 0.4: variant = 'big'
                    elif v_rand < 0.7: variant = 'medium'
                    else: variant = 'small'
                    
                    sprites.append(Tree((world_x, world_y), [self.camera_group], self.obstacles_group, variant=variant))
                
                # 2. Big Rock (Obstacle)
                elif rand_val < rock_target: 
                    from .entities.rock import Rock
                    rock = Rock((world_x, world_y), [self.camera_group], self.obstacles_group)
                    sprites.append(rock)       
        self.active_chunks[coord] = sprites

    def unload_chunk(self, coord):
        if coord in self.active_chunks:
            for sprite in self.active_chunks[coord]:
                sprite.kill()
            del self.active_chunks[coord]

    def reset(self):
        """Clears all active chunks and kills their sprites for a fresh start."""
        coords = list(self.active_chunks.keys())
        for coord in coords:
            self.unload_chunk(coord)
        self.active_chunks.clear()
