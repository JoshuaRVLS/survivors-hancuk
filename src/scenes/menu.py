import pygame
import random
from ..settings import *
from .scene import Scene

class Particle:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(1, 3)
        self.color = list(COLORS["ACCENT"])
        self.speed = random.uniform(0.2, 1.0)
        self.alpha = random.randint(50, 150)

    def update(self, dt):
        self.y -= self.speed * dt * 60
        if self.y < 0:
            self.y = SCREEN_HEIGHT
            self.x = random.randint(0, SCREEN_WIDTH)
    
    def draw(self, surface):
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((*self.color, self.alpha))
        surface.blit(s, (self.x, self.y))

class MenuScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.font_title = pygame.font.SysFont(FONT_NAME, FONT_SIZE_TITLE, bold=True)
        self.font_menu = pygame.font.SysFont(FONT_NAME, FONT_SIZE_MENU)
        
        self.options = ["Play Online", "Local Game", "Settings", "Quit"]
        self.selected_index = 0
        
        self.particles = [Particle() for _ in range(50)]
        
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    self.select_option()

    def select_option(self):
        choice = self.options[self.selected_index]
        print(f"Selected: {choice}")
        if choice == "Quit":
            self.manager.running = False
        elif choice == "Local Game":
             # Pastikan tidak ada client network
             if hasattr(self.manager, 'network_client'): delattr(self.manager, 'network_client')
             self.manager.switch_scene('char_select')
        elif choice == "Play Online":
             from ..network.client import NetworkClient
             client = NetworkClient()
             if client.connect():
                 self.manager.network_client = client
                 self.manager.switch_scene('char_select')
             else:
                 print("Gagal terhubung ke server!")

    def update(self, dt):
        for p in self.particles:
            p.update(dt)

    def draw(self):
        self.display_surface.fill(COLORS["BACKGROUND"])
        
        # Gambar Partikel
        for p in self.particles:
            p.draw(self.display_surface)
        
        # Judul
        title_surf = self.font_title.render(TITLE, True, COLORS["ACCENT"])
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))
        
        # Efek Glow untuk judul (bayangan sederhana)
        glow_surf = self.font_title.render(TITLE, True, (50, 20, 100))
        self.display_surface.blit(glow_surf, (title_rect.x + 4, title_rect.y + 4))
        self.display_surface.blit(title_surf, title_rect)
        
        # Opsi Menu
        start_y = 350
        for i, option in enumerate(self.options):
            color = COLORS["TEXT_HOVER"] if i == self.selected_index else COLORS["TEXT"]
            
            # Kotak Highlight
            if i == self.selected_index:
                opt_surf = self.font_menu.render(f"> {option} <", True, color)
            else:
                opt_surf = self.font_menu.render(option, True, color)
                
            rect = opt_surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + i * 70))
            self.display_surface.blit(opt_surf, rect)
