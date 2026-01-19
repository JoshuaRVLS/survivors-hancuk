
import pygame
from ..settings import *
from .scene import Scene

class CharacterSelectionScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = pygame.font.SysFont(FONT_NAME, 60, bold=True)
        self.font_name = pygame.font.SysFont(FONT_NAME, 40, bold=True)
        self.font_stats = pygame.font.SysFont(FONT_NAME, 24)
        
        self.char_keys = list(CHARACTER_DATA.keys())
        self.selected_index = 0
        
        # Load previews
        self.previews = {}
        for key, data in CHARACTER_DATA.items():
            try:
                from ..utils import load_sprite_sheet
                import os
                base_path = data['asset_path']
                width, height = data.get('frame_size', (96, 80))
                
                # Dynamic path resolution for preview
                path = os.path.join(base_path, "Idle", "Idle_Down.png") # Female
                if not os.path.exists(path):
                    path = os.path.join(base_path, "IDLE", "idle_down.png") # Adventurer
                
                frames = load_sprite_sheet(path, width, height, scale=4.0, trim=True)
                if frames:
                    self.previews[key] = frames[0]
                else:
                    # Generic fallback
                    self.previews[key] = pygame.Surface((100, 100))
                    self.previews[key].fill((100, 100, 100))
            except Exception as e:
                print(f"Error loading preview for {key}: {e}")
                self.previews[key] = pygame.Surface((100, 100))
                self.previews[key].fill((100, 100, 100))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_index = (self.selected_index - 1) % len(self.char_keys)
                elif event.key == pygame.K_RIGHT:
                    self.selected_index = (self.selected_index + 1) % len(self.char_keys)
                elif event.key == pygame.K_RETURN:
                    self.confirm_selection()
                elif event.key == pygame.K_ESCAPE:
                    self.manager.switch_scene('menu')

    def confirm_selection(self):
        char_key = self.char_keys[self.selected_index]
        self.manager.selected_character = char_key
        self.manager.switch_scene('game')

    def update(self, dt):
        pass

    def draw(self):
        self.display_surface.fill(COLORS["BACKGROUND"])
        
        # Title
        title_surf = self.font_title.render("SELECT YOUR HERO", True, COLORS["ACCENT"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.display_surface.blit(title_surf, title_rect)
        
        # Current Selection Card
        char_key = self.char_keys[self.selected_index]
        char_data = CHARACTER_DATA[char_key]
        
        # Preview Image
        preview = self.previews.get(char_key)
        if preview:
            prev_rect = preview.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
            # Simple bounce animation or glow could go here
            self.display_surface.blit(preview, prev_rect)
            
        # Character Info
        name_surf = self.font_name.render(char_data['name'], True, COLORS["TEXT_HOVER"])
        name_rect = name_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.display_surface.blit(name_surf, name_rect)
        
        desc_surf = self.font_stats.render(char_data['description'], True, COLORS["TEXT"])
        desc_rect = desc_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
        self.display_surface.blit(desc_surf, desc_rect)
        
        # Stats
        stats_y = SCREEN_HEIGHT // 2 + 200
        stats_text = [
            f"Health: {char_data['health']}",
            f"Speed: {char_data['speed']}",
            f"Damage: {char_data['damage']}"
        ]
        
        for i, text in enumerate(stats_text):
            s_surf = self.font_stats.render(text, True, (200, 200, 200))
            s_rect = s_surf.get_rect(center=(SCREEN_WIDTH // 2, stats_y + i * 30))
            self.display_surface.blit(s_surf, s_rect)
            
        # Navigation Hints
        hint_surf = self.font_stats.render("[LEFT/RIGHT] Change   [ENTER] Select   [ESC] Back", True, (100, 100, 100))
        hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.display_surface.blit(hint_surf, hint_rect)
