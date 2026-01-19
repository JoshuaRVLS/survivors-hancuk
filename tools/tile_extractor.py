import pygame
import sys
import os
from tkinter import filedialog, Tk, simpledialog

# Initialize Pygame and Tkinter
pygame.init()
root = Tk()
root.withdraw() # Hide the main tkinter window

class TileExtractor:
    def __init__(self):
        self.screen_width = 1200
        self.screen_height = 800
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Tile Extractor Tool")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 18)
        self.bold_font = pygame.font.SysFont("Arial", 20, bold=True)
        
        # State
        self.image = None
        self.image_rect = None
        self.tileset_path = ""
        self.tile_w = 16
        self.tile_h = 16
        self.selected_tiles = set() # (col, row)
        self.offset = pygame.math.Vector2(0, 0)
        self.zoom = 1.0
        
        # Paths
        self.export_dir = "assets/tiles"
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            
    def guess_tile_size(self):
        if not self.image: return 16, 16
        w, h = self.image_rect.width, self.image_rect.height
        
        # 1. Perfect small square (e.g., 32x32, 64x64, 128x128)
        if w == h and w <= 512 and (w & (w - 1)) == 0:
            return w, h
            
        # 2. Common power-of-two check
        for size in [128, 64, 32, 16]:
            if w % size == 0 and h % size == 0:
                if size == 128 and (w > 512 or h > 512): continue
                return size, size
                
        return 16, 16

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg")])
        if path:
            self.tileset_path = path
            self.image = pygame.image.load(path).convert_alpha()
            self.image_rect = self.image.get_rect()
            self.selected_tiles.clear()
            self.zoom = 1.0
            self.offset = pygame.math.Vector2(50, 50)
            
            # Smart Guess
            gw, gh = self.guess_tile_size()
            init_val = f"{gw},{gh}"
            
            # Ask for tile size
            res = simpledialog.askstring("Input", f"Enter Tile Size (W,H) [Suggested: {init_val}]:", initialvalue=init_val)
            if res:
                try:
                    if "," in res:
                        w, h = map(int, res.split(","))
                        self.tile_w, self.tile_h = w, h
                    else:
                        size = int(res)
                        self.tile_w, self.tile_h = size, size
                except ValueError:
                    pass

    def export_tiles(self):
        if not self.image or not self.selected_tiles:
            return
            
        # 1. Ask for filename
        file_name = simpledialog.askstring("Export", "Enter filename (without .png):", initialvalue="new_tileset")
        if not file_name:
            return
            
        print(f"Exporting {len(self.selected_tiles)} tiles to {file_name}.png (Preserving Rows)...")
        
        # 2. Group tiles by source row
        from collections import defaultdict
        rows_map = defaultdict(list)
        for col, row in self.selected_tiles:
            rows_map[row].append(col)
            
        # 3. Sort rows and columns
        sorted_row_indices = sorted(rows_map.keys())
        max_cols = 0
        for r in sorted_row_indices:
            rows_map[r].sort()
            max_cols = max(max_cols, len(rows_map[r]))
            
        num_rows = len(sorted_row_indices)
        
        # 4. Create Atlas Surface
        atlas_surf = pygame.Surface((max_cols * self.tile_w, num_rows * self.tile_h), pygame.SRCALPHA)
        
        # 5. Fill Atlas
        for new_row_idx, src_row_idx in enumerate(sorted_row_indices):
            for new_col_idx, src_col_idx in enumerate(rows_map[src_row_idx]):
                # Target position in atlas
                atlas_x = new_col_idx * self.tile_w
                atlas_y = new_row_idx * self.tile_h
                
                # Source position in sheet
                src_x = src_col_idx * self.tile_w
                src_y = src_row_idx * self.tile_h
                
                atlas_surf.blit(self.image, (atlas_x, atlas_y), (src_x, src_y, self.tile_w, self.tile_h))
            
        # 6. Save
        export_path = os.path.join(self.export_dir, f"{file_name}.png")
        pygame.image.save(atlas_surf, export_path)
            
        print(f"Export Complete! Saved to {export_path}")
        self.selected_tiles.clear()

    def run(self):
        while True:
            self.screen.fill((40, 44, 52))
            dt = self.clock.tick(60) / 1000.0
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_l:
                        self.load_image()
                    if event.key == pygame.K_e:
                        self.export_tiles()
                    if event.key == pygame.K_ESCAPE:
                        self.selected_tiles.clear()
                    if event.key == pygame.K_t:
                        # Re-open dialog
                        init_val = f"{self.tile_w},{self.tile_h}"
                        res = simpledialog.askstring("Input", f"Enter Tile Size (W,H) [Current: {init_val}]:", initialvalue=init_val)
                        if res:
                            try:
                                if "," in res:
                                    w, h = map(int, res.split(","))
                                    self.tile_w, self.tile_h = w, h
                                else:
                                    size = int(res)
                                    self.tile_w, self.tile_h = size, size
                            except ValueError: pass
                    
                    # Fine-tuning: [ ] for Width, Shift + [ ] for Height
                    step = 1
                    if pygame.key.get_mods() & pygame.KMOD_ALT: # Faster tuning with Alt
                        step = 8
                        
                    if event.key == pygame.K_LEFTBRACKET:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            self.tile_h = max(1, self.tile_h - step)
                        else:
                            self.tile_w = max(1, self.tile_w - step)
                    if event.key == pygame.K_RIGHTBRACKET:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            self.tile_h = min(512, self.tile_h + step)
                        else:
                            self.tile_w = min(512, self.tile_w + step)
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left Click: Select
                        if self.image:
                            mx, my = pygame.mouse.get_pos()
                            # Convert mouse to image space
                            img_x = (mx - self.offset.x) / self.zoom
                            img_y = (my - self.offset.y) / self.zoom
                            
                            if 0 <= img_x < self.image_rect.width and 0 <= img_y < self.image_rect.height:
                                col = int(img_x // self.tile_w)
                                row = int(img_y // self.tile_h)
                                if (col, row) in self.selected_tiles:
                                    self.selected_tiles.remove((col, row))
                                else:
                                    self.selected_tiles.add((col, row))
                                    
                    if event.button == 4: # Scroll Up: Zoom
                        self.zoom = min(4.0, self.zoom + 0.1)
                    if event.button == 5: # Scroll Down: Zoom
                        self.zoom = max(0.5, self.zoom - 0.1)

                # Pan with Middle Mouse
                if pygame.mouse.get_pressed()[1]:
                    rel = pygame.mouse.get_rel()
                    self.offset += pygame.math.Vector2(rel)
                else:
                    pygame.mouse.get_rel() # Reset rel

            # Draw Image
            if self.image:
                scaled_size = (int(self.image_rect.width * self.zoom), int(self.image_rect.height * self.zoom))
                scaled_img = pygame.transform.scale(self.image, scaled_size)
                self.screen.blit(scaled_img, self.offset)
                
                # Visual Tile Size (Pixels on screen)
                v_tile_w = self.tile_w * self.zoom
                v_tile_h = self.tile_h * self.zoom
                
                # Hover Highlight
                mx, my = pygame.mouse.get_pos()
                img_x = (mx - self.offset.x) / self.zoom
                img_y = (my - self.offset.y) / self.zoom
                
                if 0 <= img_x < self.image_rect.width and 0 <= img_y < self.image_rect.height:
                    hover_col = int(img_x // self.tile_w)
                    hover_row = int(img_y // self.tile_h)
                    
                    hover_rect = pygame.Rect(
                        self.offset.x + hover_col * v_tile_w,
                        self.offset.y + hover_row * v_tile_h,
                        v_tile_w,
                        v_tile_h
                    )
                    pygame.draw.rect(self.screen, (255, 255, 255), hover_rect, 1)
                    
                    # Show coords near mouse
                    c_surf = self.font.render(f"({hover_col}, {hover_row})", True, (255, 255, 255))
                    self.screen.blit(c_surf, (mx + 15, my + 5))

                # Draw Grid
                cols = self.image_rect.width // self.tile_w
                rows = self.image_rect.height // self.tile_h
                
                for c in range(cols + 1):
                    x = self.offset.x + c * v_tile_w
                    pygame.draw.line(self.screen, (80, 80, 80, 50), (x, self.offset.y), (x, self.offset.y + self.image_rect.height * self.zoom))
                for r in range(rows + 1):
                    y = self.offset.y + r * v_tile_h
                    pygame.draw.line(self.screen, (80, 80, 80, 50), (self.offset.x, y), (self.offset.x + self.image_rect.width * self.zoom, y))

                # Draw Selections
                for col, row in self.selected_tiles:
                    rect = pygame.Rect(
                        self.offset.x + col * v_tile_w,
                        self.offset.y + row * v_tile_h,
                        v_tile_w,
                        v_tile_h
                    )
                    pygame.draw.rect(self.screen, (0, 255, 120), rect, 3) 
                    pygame.draw.rect(self.screen, (0, 255, 120), rect, 1)

                    
            # UI Overlay
            self.draw_ui()
            
            pygame.display.flip()

    def draw_ui(self):
        # Background bar
        pygame.draw.rect(self.screen, (30, 30, 35), (0, 0, self.screen_width, 40))
        
        instructions = [
            ("L", "Load"),
            ("E", "Export"),
            ("T", "Set W,H"),
            ("[ ]", "Width"),
            ("Shift+[ ]", "Height"),
            ("ESC", "Clear"),
        ]
        
        x_off = 10
        for key, desc in instructions:
            k_surf = self.bold_font.render(key, True, (0, 255, 200))
            self.screen.blit(k_surf, (x_off, 10))
            x_off += k_surf.get_width() + 5
            
            d_surf = self.font.render(f": {desc}  |", True, (255, 255, 255))
            self.screen.blit(d_surf, (x_off, 10))
            x_off += d_surf.get_width() + 15

        if self.image:
            stats = f"Img: {self.image_rect.width}x{self.image_rect.height} | Tile: {self.tile_w}x{self.tile_h} | Selected: {len(self.selected_tiles)}"
            s_surf = self.font.render(stats, True, (255, 200, 0))
            self.screen.blit(s_surf, (self.screen_width - s_surf.get_width() - 10, 10))

if __name__ == "__main__":
    extractor = TileExtractor()
    extractor.run()
