import pygame
import sys
from .settings import *
from .shaders import ShaderPipeline
from .utils import debug_log
from .scenes.menu import MenuScene
from .scenes.char_select import CharacterSelectionScene
from .scenes.game import GameScene

class GameManager:
    def __init__(self):
        pygame.init()
        # State Layar
        self.res_index = 0
        self.resolution = RESOLUTIONS[self.res_index]
        self.fullscreen = False
        
        # Setup Window Awal
        self.apply_display_settings()
        
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Manajemen Scene
        self.selected_character = 'adventurer'
        self.scenes = {
            'menu': MenuScene(self),
            'char_select': CharacterSelectionScene(self),
            'game': GameScene(self)
        }
        self.active_scene = self.scenes['menu']
        
        # State Global
        self.is_hit_stopped = False
        self.hit_stop_timer = 0
        
        # Akses global untuk entity (Hit Stop, dll)
        import __main__
        __main__.game = self
        
        # State Debug Runtime (Mutable)
        self.debug_mode = DEBUG_MODE
        
    def apply_display_settings(self):
        flags = pygame.OPENGL | pygame.DOUBLEBUF
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
            
        self.screen = pygame.display.set_mode(self.resolution, flags)
        self.render_surface = pygame.Surface(self.resolution)
        self.ui_surface = pygame.Surface(self.resolution, pygame.SRCALPHA) # Layer UI Transparan
        
        if hasattr(self, 'shaders'):
            self.shaders.resize(self.resolution)
        else:
            self.shaders = ShaderPipeline(self.resolution)
            
        debug_log(f"Display Settings Applied: {self.resolution}, Fullscreen: {self.fullscreen}")

    def switch_scene(self, scene_key):
        if scene_key in self.scenes:
            debug_log(f"Switching Scene: {getattr(self.active_scene, '__class__', {}).__name__} -> {scene_key}")
            self.active_scene = self.scenes[scene_key]
            self.active_scene.on_enter()
            self.clock.tick(FPS) 
        
    def run(self):
        while self.running:
            # Hitung Delta Time sekali per frame
            dt = self.clock.tick(FPS) / 1000.0
            # Cap keamanan: Jangan pernah lompat lebih dari 1/15 detik untuk cegah tunneling
            dt = min(dt, 0.066) 
            
            # Logika Hit Stop
            can_update = True
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Oper event ke scene aktif
                self.active_scene.handle_events([event])
                
            # Update Scene Aktif dengan dt yang di-cap
            if can_update:
                self.active_scene.update(dt)
            
            # Tentukan posisi pemain di layar untuk shader lighting
            player_screen_pos = (0.5, 0.5)
            if isinstance(self.active_scene, GameScene) and hasattr(self.active_scene, 'player'):
                # Posisi pemain dalam koordinat virtual surface
                # (player_center - camera_offset) / virtual_surface_size
                cam = self.active_scene.camera_group
                virtual_size = self.active_scene.virtual_width, self.active_scene.virtual_height
                
                # PAKSA Tengah untuk sekarang untuk atasi bug "Kiri Atas".
                # Kamera menjaga pemain tetap di tengah.
                player_screen_pos = (0.5, 0.5)
            
            # Gambar Scene Aktif (Bisa mengembalikan bar_data untuk shader)
            self.ui_surface.fill((0, 0, 0, 0)) # Bersihkan UI dari frame sebelumnya
            bar_data = self.active_scene.draw()
            
            # Tentukan mode render
            # 0: Game (Lighting), 1: Menu (Full Bright)
            render_mode = 0
            lights = []
            shadows = []
            from .scenes.menu import MenuScene
            from .scenes.char_select import CharacterSelectionScene
            if isinstance(self.active_scene, MenuScene) or isinstance(self.active_scene, CharacterSelectionScene):
                render_mode = 1
            elif isinstance(self.active_scene, GameScene) and getattr(self.active_scene, 'level_up_active', False):
                render_mode = 2
            else:
                # Koleksi Cahaya Teroptimasi
                if hasattr(self.active_scene, 'light_sprites'):
                    cam = self.active_scene.camera_group
                    virtual_size = self.active_scene.virtual_width, self.active_scene.virtual_height
                    
                    for sprite in self.active_scene.light_sprites:
                        # Cek keamanan posisi
                        if hasattr(sprite, 'pos'):
                            s_pos = sprite.pos
                        elif hasattr(sprite, 'rect'):
                            s_pos = pygame.math.Vector2(sprite.rect.center)
                        else:
                            continue

                        # Normalisasi posisi cahaya
                        lx = (s_pos.x - cam.offset.x) / virtual_size[0]
                        ly = (s_pos.y - cam.offset.y) / virtual_size[1]
                        # Culling sederhana: hanya tambah jika di/dekat layar (0..1)
                        if -0.2 < lx < 1.2 and -0.2 < ly < 1.2:
                            rad = getattr(sprite, 'radius', 100) 
                            # Konversi warna 0-255 ke 0-1.0 float jika ditemukan
                            col = getattr(sprite, 'color', (255, 255, 255))
                            if isinstance(col, tuple) and len(col) >= 3:
                                col_f = (col[0]/255.0, col[1]/255.0, col[2]/255.0)
                            else:
                                col_f = col # Anggap sudah ternormalisasi jika float
                            lights.append((lx, ly, rad / virtual_size[0], col_f))

                # Kalkulasi Bayangan (Chest)
                if hasattr(self.active_scene, 'interactable_sprites'):
                    cam = self.active_scene.camera_group
                    virtual_size = self.active_scene.virtual_width, self.active_scene.virtual_height
                    
                    for sprite in self.active_scene.interactable_sprites:
                        # Normalisasi posisi
                        # Offset ke Bawah (+18) relatif terhadap tengah
                        # Catatan: +Y adalah bawah di koordinat layar
                        sx = (sprite.rect.centerx - cam.offset.x) / virtual_size[0]
                        sy = (sprite.rect.centery + 18 - cam.offset.y) / virtual_size[1]
                        
                        # Culling
                        if -0.2 < sx < 1.2 and -0.2 < sy < 1.2:
                            shadows.append((sx, sy, 0.05)) # Radius diperbesar
                
            # Render via Pipeline Shader (Kirim world, UI, dan Shadows)
            self.shaders.render(
                self.render_surface, 
                ui_surface=self.ui_surface, 
                player_pos=player_screen_pos, 
                render_mode=render_mode, 
                lights=lights, 
                shadows=shadows,
                bar_data=bar_data
            )
            
            pygame.display.flip()
            # JANGAN tick lagi di sini! Baris 42 sudah menanganinya.
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = GameManager()
    game.run()
