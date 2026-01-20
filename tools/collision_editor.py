
import pygame
import json
import os
import sys

# Menambahkan directory root ke path agar bisa import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.settings import *
from src.utils import load_sprite_sheet

class CollisionEditor:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1000, 800))
        pygame.display.set_caption("Antigravity Collision Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 18)
        self.running = True

        # Editor State
        self.data_path = "assets/data/collisions.json"
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        self.collisions = self.load_data()
        
        # Entity Selection
        self.entities = list(ENEMY_DATA.keys()) + list(CHARACTER_DATA.keys())
        self.entity_index = 0
        self.current_entity = self.entities[self.entity_index]
        
        # Sprite Loading
        self.base_sprite = None # Original loaded image before zoom
        self.zoom = 1.0
        self.load_current_sprite()
        
        # Vertex Editing
        self.vertices = self.collisions.get(self.current_entity, {"type": "poly", "points": []})["points"]
        self.selected_vertex = None
        self.dragging_all = False
        self.drag_offset = (0, 0)
        self.last_mouse_pos = (0, 0)
        
        # Grid settings
        self.grid_size = 1
        self.snap_to_grid = True

    def load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, "r") as f:
                return json.load(f)
        return {}

    def save_data(self):
        self.collisions[self.current_entity] = {
            "type": "poly", 
            "points": self.vertices,
            "ref_size": self.sprite.get_size()
        }
        with open(self.data_path, "w") as f:
            json.dump(self.collisions, f, indent=4)
        print(f"Saved {self.current_entity} collision data!")

    def load_current_sprite(self):
        self.current_entity = self.entities[self.entity_index]
        data = ENEMY_DATA.get(self.current_entity) or CHARACTER_DATA.get(self.current_entity)
        
        path = data['asset_path']
        self.base_scale = data.get('scale', 2.0) if 'scale' in data else 2.5
        
        try:
            full_path = ""
            sub_idles = [d for d in os.listdir(path) if d.lower() == "idle" and os.path.isdir(os.path.join(path, d))]
            
            if sub_idles:
                idle_dir = os.path.join(path, sub_idles[0])
                files = os.listdir(idle_dir)
                found_file = next(f for f in files if f.endswith(".png") and ("idle" in f.lower() or "down" in f.lower()))
                full_path = os.path.join(idle_dir, found_file)
            else:
                files = os.listdir(path)
                found_file = next(f for f in files if f.endswith(".png") and "idle" in f.lower())
                full_path = os.path.join(path, found_file)

            w, h = 100, 100
            if "frame_size" in data: w, h = data["frame_size"]
            elif "female" in self.current_entity: w, h = 48, 64
            
            # Load with base scale
            sprites = load_sprite_sheet(full_path, w, h, scale=self.base_scale, trim=False)
            self.base_sprite = sprites[0]
            self.apply_zoom()
        except Exception as e:
            print(f"Error loading sprite for {self.current_entity}: {e}")
            self.base_sprite = pygame.Surface((100, 100))
            self.base_sprite.fill((255, 0, 255))
            self.apply_zoom()
            
        # Refresh vertices
        self.vertices = self.collisions.get(self.current_entity, {"type": "poly", "points": []})["points"]

    def apply_zoom(self):
        if not self.base_sprite: return
        w, h = self.base_sprite.get_size()
        new_size = (int(w * self.zoom), int(h * self.zoom))
        self.sprite = pygame.transform.scale(self.base_sprite, new_size)
        self.sprite_rect = self.sprite.get_rect(center=(500, 400))

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            self.handle_events()
            self.update()
            self.draw()

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    self.save_data()
                if event.key == pygame.K_RIGHT:
                    self.entity_index = (self.entity_index + 1) % len(self.entities)
                    self.zoom = 1.0
                    self.load_current_sprite()
                if event.key == pygame.K_LEFT:
                    self.entity_index = (self.entity_index - 1) % len(self.entities)
                    self.zoom = 1.0
                    self.load_current_sprite()
                if event.key == pygame.K_c:
                    self.vertices = []
                if event.key == pygame.K_DELETE and self.selected_vertex is not None:
                    self.vertices.pop(self.selected_vertex)
                    self.selected_vertex = None

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4: # Scroll Up (Zoom In)
                    self.zoom = min(5.0, self.zoom + 0.1)
                    self.apply_zoom()
                if event.button == 5: # Scroll Down (Zoom Out)
                    self.zoom = max(0.5, self.zoom - 0.1)
                    self.apply_zoom()

                if event.button == 1: # Left Click
                    # Check for vertex selection - scaled radius
                    found = False
                    hit_radius = 15 * self.zoom
                    for i, p in enumerate(self.vertices):
                        world_p = (p[0] * self.zoom + self.sprite_rect.x, p[1] * self.zoom + self.sprite_rect.y)
                        if pygame.math.Vector2(world_p).distance_to(mouse_pos) < hit_radius:
                            self.selected_vertex = i
                            self.drag_offset = (world_p[0] - mouse_pos[0], world_p[1] - mouse_pos[1])
                            found = True
                            break
                    
                    if not found:
                        rel_x = (mouse_pos[0] - self.sprite_rect.x) / self.zoom
                        rel_y = (mouse_pos[1] - self.sprite_rect.y) / self.zoom
                        if self.snap_to_grid:
                            rel_x = round(rel_x / self.grid_size) * self.grid_size
                            rel_y = round(rel_y / self.grid_size) * self.grid_size
                        self.vertices.append([rel_x, rel_y])
                        self.selected_vertex = len(self.vertices) - 1
                        self.drag_offset = (0, 0)
                
                if event.button == 3: # Right Click
                    self.dragging_all = True
                    self.last_mouse_pos = mouse_pos

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.selected_vertex = None
                if event.button == 3:
                    self.dragging_all = False

    def update(self):
        mouse_pos = pygame.mouse.get_pos()
        
        # 1. Move Single Vertex
        if self.selected_vertex is not None:
            dragged_world_x = mouse_pos[0] + self.drag_offset[0]
            dragged_world_y = mouse_pos[1] + self.drag_offset[1]
            
            rel_x = (dragged_world_x - self.sprite_rect.x) / self.zoom
            rel_y = (dragged_world_y - self.sprite_rect.y) / self.zoom
            
            if self.snap_to_grid:
                rel_x = round(rel_x / self.grid_size) * self.grid_size
                rel_y = round(rel_y / self.grid_size) * self.grid_size
            self.vertices[self.selected_vertex] = [rel_x, rel_y]
            
        # 2. Move All Vertices
        if self.dragging_all:
            dx = (mouse_pos[0] - self.last_mouse_pos[0]) / self.zoom
            dy = (mouse_pos[1] - self.last_mouse_pos[1]) / self.zoom
            
            for i in range(len(self.vertices)):
                self.vertices[i][0] += dx
                self.vertices[i][1] += dy
            
            self.last_mouse_pos = mouse_pos

    def draw(self):
        self.screen.fill((30, 30, 40))
        
        # Render Sprite
        self.screen.blit(self.sprite, self.sprite_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), self.sprite_rect, 1)
        
        # Render Vertices
        if len(self.vertices) > 1:
            points = [(p[0] * self.zoom + self.sprite_rect.x, p[1] * self.zoom + self.sprite_rect.y) for p in self.vertices]
            pygame.draw.polygon(self.screen, (0, 255, 0), points, 2)
        
        for i, p in enumerate(self.vertices):
            color = (255, 255, 0) if i == self.selected_vertex else (255, 0, 0)
            world_p = (p[0] * self.zoom + self.sprite_rect.x, p[1] * self.zoom + self.sprite_rect.y)
            pygame.draw.circle(self.screen, color, world_p, 3)
            
        # UI
        info = [
            f"Entity: {self.current_entity} ({self.entity_index + 1}/{len(self.entities)})",
            f"Zoom: {self.zoom:.1f}x",
            "Scroll: Zoom In/Out",
            "Left Click: Add/Move Vertex",
            "Right Click Drag: Move All",
            "Delete: Remove Selected Vertex",
            "C: Clear All",
            "S: Save JSON",
            "Arrows: Cycle Entities"
        ]
        for i, line in enumerate(info):
            txt = self.font.render(line, True, (255, 255, 255))
            self.screen.blit(txt, (10, 10 + i * 22))
            
        pygame.display.flip()

if __name__ == "__main__":
    editor = CollisionEditor()
    editor.run()
