import pygame
import random
from ..settings import *
from ..items.upgrades import UPGRADE_DATA
from ..entities.player import Player
from ..entities.enemy import Enemy
from ..camera import CameraGroup
from ..tilemap import ChunkManager
from .scene import Scene

class GameScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        
        # Virtual Display untuk Zoom
        # Logic CameraGroup mandiri atau pakai surface manager
        # CATATAN: Game.py sebelumnya membuat surface display SENDIRI.
        # Kita adaptasi itu.
        
        self.virtual_width = SCREEN_WIDTH
        self.virtual_height = SCREEN_HEIGHT
        self.virtual_surface = self.manager.render_surface
        
        # Kamera & Grup Sprite
        self.camera_group = CameraGroup(self.virtual_surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.light_sprites = pygame.sprite.Group() # Group teroptimasi untuk shader
        self.remote_players = pygame.sprite.Group() # Multiplayer
        
        # Manajer Chunk Tak Terbatas (Lantai Prosedural)
        from ..tilemap import ChunkManager
        self.chunk_manager = ChunkManager(
            self.camera_group, 
            self.obstacle_sprites
        )
        
        # Spawn pemain (Di mana saja)
        self.player = Player((0, 0), self.camera_group, self.obstacle_sprites, self.enemy_sprites, self.manager.selected_character)
        
        # Link Kamera ke Pemain
        self.camera_group.target = self.player
        
    def on_enter(self):
        # 0. RESET STATE TOTAL
        # Hapus semua sprite yang ada
        for sprite in self.camera_group: sprite.kill()
        self.camera_group.empty()
        self.obstacle_sprites.empty()
        self.enemy_sprites.empty()
        self.light_sprites.empty()
        if hasattr(self, 'interactable_sprites'): self.interactable_sprites.empty()
        
        # Reset Manajer Chunk (Regenerasi Dunia)
        self.chunk_manager.reset()
        
        # Mulai baru untuk pemain dengan karakter terpilih
        # (Pemain akan menambahkan dirinya sendiri ke camera_group dan grup lain di __init__)
        self.player = Player((0, 0), self.camera_group, self.obstacle_sprites, self.enemy_sprites, self.manager.selected_character)
        self.camera_group.target = self.player
        
        # Reset difficulty dan timer
        self.survival_start_time = pygame.time.get_ticks()
        self.difficulty_multiplier = 1.0
        self.difficulty_timer = self.survival_start_time
        self.spawn_timer = 0
        self.spawn_cooldown = INITIAL_SPAWN_COOLDOWN
        
        self.paused = False
        self.level_up_active = False
        self.upgrade_options = []
        self.auto_attack = True # Default ON
        self.menu_options = ["Resume", "Auto-Attack: ON", "Fullscreen: OFF", "Resolution: 1280x720", "Quit to Menu"]
        self.menu_index = 0
        
        # Cache Ikon Upgrade
        self.upgrade_icons = {}

        
        # Font Debug (Dicache)
        self.debug_font = pygame.font.SysFont("arial", 16)
        
        # Minimap (Refactor)
        from ..ui.minimap import Minimap
        self.minimap = Minimap(self.manager, self.player)

        # Interactables (Removed per User Request)
        self.interactable_sprites = pygame.sprite.Group()
        # self.spawn_initial_chests()
        
    def spawn_initial_chests(self):
        from ..entities.interactables import Chest
        count = 0
        while count < 5: # Dikurangi dari 10
            x = random.uniform(-1200, 1200)
            y = random.uniform(-1200, 1200)
            
            # Cek Jarak (Jangan spawn terlalu dekat start)
            if pygame.math.Vector2(x, y).magnitude() > 300:
                Chest((x, y), [self.camera_group, self.obstacle_sprites, self.interactable_sprites])
                Chest((x, y), [self.camera_group, self.obstacle_sprites, self.interactable_sprites])
                count += 1

    def update_network(self):
        client = getattr(self.manager, 'network_client', None)
        if not client or not client.connected: return

        # 1. Kirim State Lokal
        state = {
            'pos': (self.player.pos.x, self.player.pos.y),
            'status': self.player.status,
            'char_type': self.manager.selected_character # Kirim KEY (misal 'female') bukan Nama
        }
        client.send_state(state)
        
        # 2. Sinkronisasi Remote Players
        # client.other_players adalah dict: {pid: {pos, status, char_type}}
        active_pids = set()
        
        for pid, data in client.other_players.items():
            active_pids.add(pid)
            
            # Cek jika ada
            r_player = None
            for rp in self.remote_players:
                if rp.pid == pid:
                    r_player = rp
                    break
            
            if not r_player:
                # Spawn Baru
                from ..entities.remote_player import RemotePlayer
                c_type = data.get('char_type', 'adventurer')
                r_player = RemotePlayer(pid, [self.camera_group, self.remote_players], char_type=c_type)
            
            # Update
            r_player.update_state(data['pos'], data['status'], data.get('char_type'))

        # 3. Proses Event
        with client.lock:
            while client.events:
                evt = client.events.pop(0)
                if evt['event'] == 'attack':
                    sender_id = evt['sender']
                    # Cari pemain
                    for rp in self.remote_players:
                        if rp.pid == sender_id:
                            rp.perform_attack(evt['weapon'], evt['angles'])
                            break
                            
                elif evt['event'] == 'spawn_enemy':
                    # Spawn di sisi Client
                    uid = evt['uid']
                    # Cek duplikat
                    exists = False
                    for e in self.enemy_sprites:
                        if hasattr(e, 'uid') and e.uid == uid:
                             exists = True; break
                    
                    if not exists:
                        Enemy(evt['pos'], [self.camera_group, self.enemy_sprites], self.player, self.obstacle_sprites, evt['type'], evt['diff'], uid=uid)

                elif evt['event'] == 'kill_enemy':
                    uid = evt['uid']
                    for e in self.enemy_sprites:
                        if hasattr(e, 'uid') and e.uid == uid:
                             # Langsung kill diam-diam atau picu death?
                             # Picu death memungkinkan animasi
                             if not e.is_dead:
                                 e.health = 0
                                 e.is_dead = True
                                 e.frame_index = 0
                                 e.status = 'death'
                             break

        # 4. Bersihkan yang Terputus
        for rp in self.remote_players:
            if rp.pid not in active_pids:
                rp.kill()
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Fix: If level up is active, ESC should NOT close the menu or toggle pause
                    if not self.level_up_active:
                        self.paused = not self.paused
                elif event.key == pygame.K_BACKQUOTE:
                    self.manager.debug_mode = not self.manager.debug_mode
                elif event.key == pygame.K_e:
                    self.handle_interaction()
                
                if self.paused:
                    if event.key == pygame.K_UP:
                        self.menu_index = (self.menu_index - 1) % len(self.menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.menu_index = (self.menu_index + 1) % len(self.menu_options)
                    elif event.key == pygame.K_RETURN:
                        self.select_menu_option()
                        if not self.manager.running: return # Handle quit

                if self.level_up_active:
                    if event.key == pygame.K_1 and len(self.upgrade_options) > 0: self.apply_upgrade(self.upgrade_options[0])
                    elif event.key == pygame.K_2 and len(self.upgrade_options) > 1: self.apply_upgrade(self.upgrade_options[1])
                    elif event.key == pygame.K_3 and len(self.upgrade_options) > 2: self.apply_upgrade(self.upgrade_options[2])

            if event.type == pygame.MOUSEBUTTONDOWN and self.paused:
                mouse_pos = pygame.mouse.get_pos()
                
                if self.level_up_active:
                    # Check collision with cards
                    sw, sh = self.manager.resolution
                    card_w, card_h = 250, 350
                    gap = 40
                    total_w = 3 * card_w + 2 * gap
                    start_x = (sw - total_w) // 2
                    cls_y = (sh - card_h) // 2
                    
                    for i, opt in enumerate(self.upgrade_options):
                        rect = pygame.Rect(start_x + i*(card_w+gap), cls_y, card_w, card_h)
                        if rect.collidepoint(mouse_pos):
                            self.apply_upgrade(opt)
                            break
                else:
                    # Pause Menu Clicks
                    sw, sh = self.manager.resolution
                    font_o = pygame.font.SysFont('arial', 32)
                    start_y = 300
                    for i, option in enumerate(self.menu_options):
                        # Use a reasonable fixed width for the click area
                        rect = pygame.Rect(0, 0, 400, 50)
                        rect.center = (sw // 2, start_y + i * 60)
                        if rect.collidepoint(mouse_pos):
                            self.menu_index = i
                            self.select_menu_option()
                            break

    def trigger_level_up(self):
        self.paused = True
        self.level_up_active = True
        
        # Filter Upgrade Valid
        valid_pool = []
        possible = list(UPGRADE_DATA.values())
        
        for opt in possible:
            # Cek 'req_weapon' (Harus PUNYA)
            if 'req_weapon' in opt:
                 req = opt['req_weapon']
                 if req not in self.player.weapons:
                     continue
            
            # Cek 'req_missing' (Harus TIDAK PUNYA)
            if 'req_missing' in opt:
                 req = opt['req_missing']
                 if req in self.player.weapons:
                     continue
            
            valid_pool.append(opt)
            
        # Pilih 3 upgrade unik dari pool valid
        if len(valid_pool) < 3:
             self.upgrade_options = valid_pool
        else:
             self.upgrade_options = random.sample(valid_pool, 3)
        
    def apply_upgrade(self, opt):
        # 1. Handle Unlock
        if opt['op'] == 'unlock':
             weapon_id = opt['value']
             # Add to player inventory
             if weapon_id in WEAPON_DATA:
                  self.player.weapons[weapon_id] = WEAPON_DATA[weapon_id].copy()
                  print(f"UNLOCKED WEAPON: {weapon_id}")
             else:
                  print(f"ERROR: Weapon ID {weapon_id} not found in DATA")
             
             # Resume
             self._post_upgrade()
             return

        # 2. Identify Target
        target_obj = self.player
        target_str = opt['target']
        
        if target_str == 'weapon':
             # Main weapon (Backwards compat)
             target_obj = self.player.weapon_data
        elif target_str.startswith('weapon.'):
             # Specific weapon (e.g. weapon.aura)
             wid = target_str.split('.')[1]
             if wid in self.player.weapons:
                  target_obj = self.player.weapons[wid]
             else:
                  print(f"ERROR: Targeting missing weapon {wid}")
                  self._post_upgrade()
                  return
        
        # 3. Apply Value
        val = opt['value']
        stat = opt['stat']
        
        curr = target_obj.get(stat, 0) if isinstance(target_obj, dict) else getattr(target_obj, stat)
        
        if opt['op'] == 'add':
            new_val = curr + val
        elif opt['op'] == 'mult':
            new_val = curr * val
        elif opt['op'] == 'add_heal':
             new_val = curr + val
             self.player.health += val
        
        # Apply
        if isinstance(target_obj, dict):
            target_obj[stat] = int(new_val) if stat == 'projectile_count' else new_val
        else:
            setattr(target_obj, stat, new_val)
            
        print(f"Applied Upgrade: {opt['name']} -> {stat} now {new_val}")
        
        self._post_upgrade()

    def _post_upgrade(self):
        # Resume
        self.level_up_active = False
        self.paused = False
        
        # Check if more XP remains (re-trigger)
        if self.player.exp >= self.player.exp_required:
            self.player.gain_exp(0) # Logic triggers again

    def select_menu_option(self):
        choice = self.menu_options[self.menu_index]
        if "Resume" in choice:
            self.paused = False
        elif "Auto-Attack" in choice:
            self.auto_attack = not self.auto_attack
            self.update_menu_text()
        elif "Fullscreen" in choice:
            self.manager.fullscreen = not self.manager.fullscreen
            self.manager.apply_display_settings()
            self.update_menu_text()
        elif "Resolution" in choice:
            self.manager.res_index = (self.manager.res_index + 1) % len(RESOLUTIONS)
            self.manager.resolution = RESOLUTIONS[self.manager.res_index]
            self.manager.apply_display_settings()
            self.update_menu_text()
        elif "Quit" in choice:
            self.manager.switch_scene('menu')

    def update_menu_text(self):
        aa_text = "ON" if self.auto_attack else "OFF"
        fs_text = "ON" if self.manager.fullscreen else "OFF"
        res_text = f"{self.manager.resolution[0]}x{self.manager.resolution[1]}"
        self.menu_options[1] = f"Auto-Attack: {aa_text}"
        self.menu_options[2] = f"Fullscreen: {fs_text}"
        self.menu_options[3] = f"Resolution: {res_text}"

    def update(self, dt):
        if self.paused:
            return

        # Entity Updates
        self.camera_group.update(dt) 
        self.interactable_sprites.update(dt)

        current_time = pygame.time.get_ticks()

        # Update Difficulty
        if current_time - self.difficulty_timer > DIFFICULTY_INTERVAL:
            self.difficulty_multiplier += DIFFICULTY_RAMP_RATE
            self.difficulty_timer = current_time
            # Reduce spawn cooldown
            self.spawn_cooldown = max(MIN_SPAWN_COOLDOWN, INITIAL_SPAWN_COOLDOWN / self.difficulty_multiplier)
            print(f"Difficulty increased! Multiplier: {self.difficulty_multiplier:.2f}, Spawn Cooldown: {self.spawn_cooldown:.0f}ms")

        # Death Reset Logic
        if self.player.is_dead:
            # Check if animation is done (Safe get)
            death_anim = self.player.animations.get('death', [])
            if self.player.frame_index >= len(death_anim) - 1:
                if not hasattr(self, 'death_time'):
                    self.death_time = current_time
                
                if current_time - self.death_time > 1500:
                    self.player.health = self.player.max_health
                    self.player.is_dead = False
                    self.player.status = 'idle'
                    self.player.pos = pygame.math.Vector2(0, 0)
                    for enemy in self.enemy_sprites:
                        enemy.kill()
                    # Reset difficulty
                    self.difficulty_multiplier = 1.0
                    self.difficulty_timer = current_time
                    self.spawn_cooldown = INITIAL_SPAWN_COOLDOWN
                    self.survival_start_time = pygame.time.get_ticks() # Reset Timer
                    if hasattr(self, 'death_time'): delattr(self, 'death_time')
                    return
    
        # Spawn enemies (Swarm System)
        if current_time - self.spawn_timer > self.spawn_cooldown:
            self.spawn_enemy_wave(current_time)
            self.spawn_timer = current_time
            
        # Update World
        self.chunk_manager.update(self.player.pos)
        
        # Network Sync
        self.update_network()
        self.remote_players.update(dt)

    def spawn_enemy(self, pos=None):
        # Generic Spawning using ENEMY_DATA
        import math
        import uuid
        
        spawn_x, spawn_y = 0, 0
        
        if pos:
            spawn_x, spawn_y = pos
        else:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(700, 1200)
            spawn_x = self.player.pos.x + math.cos(angle) * distance
            spawn_y = self.player.pos.y + math.sin(angle) * distance
        
        # Determine enemy type
        enemy_type = 'orc'
        captain_chance = 0.02 * self.difficulty_multiplier # Start at 2%, grows with difficulty
        if random.random() < min(captain_chance, 0.4): # Cap at 40%
            enemy_type = 'orc_captain'
        
        uid = str(uuid.uuid4())
        
        # Spawn Locally
        Enemy((spawn_x, spawn_y), [self.camera_group, self.enemy_sprites], self.player, self.obstacle_sprites, enemy_type, self.difficulty_multiplier, uid=uid)

        # Broadcast if Host
        if hasattr(self.manager, 'network_client') and self.manager.network_client and self.manager.network_client.is_host:
             self.manager.network_client.send_event('spawn_enemy', {
                 'uid': uid,
                 'type': enemy_type,
                 'pos': (spawn_x, spawn_y),
                 'diff': self.difficulty_multiplier
             })

    def spawn_enemy_wave(self, current_time):
        # CEK HOST: Hanya Host yang jalankan logika spawn
        is_host = True
        if hasattr(self.manager, 'network_client') and self.manager.network_client:
            is_host = self.manager.network_client.is_host
            
        if not is_host: return # Client diam saja
        
        # Hard Cap Jumlah Musuh (Cegah lag)
        if len(self.enemy_sprites) >= 300:
            return
        
        # Hitung Waktu Bertahan
        elapsed_sec = (current_time - self.survival_start_time) // 1000
        minutes = elapsed_sec // 60
        
        # Tentukan Tipe Spawn
        import math
        import uuid
        
        # Default: Spawn Tunggal
        count = 1
        is_cluster = False
        collision_radius = 50
        
        # Logika Progresi
        if minutes >= 3:
             # Swarm Intens
             if random.random() < 0.3: # 30% peluang swarm masif
                 count = random.randint(8, 12)
                 is_cluster = True
        elif minutes >= 1:
             # Grup Periodik
             if random.random() < 0.2: # 20% peluang grup kecil
                 count = random.randint(3, 5)
                 is_cluster = True
                 
        # Eksekusi Spawn
        if is_cluster:
            # Pilih pusat cluster
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(700, 900)
            center_x = self.player.pos.x + math.cos(angle) * distance
            center_y = self.player.pos.y + math.sin(angle) * distance
            
            for _ in range(count):
                # Spawn di sekitar pusat
                offset_x = random.uniform(-100, 100)
                offset_y = random.uniform(-100, 100)
                spawn_pos = (center_x + offset_x, center_y + offset_y)
                
                # Tipe Musuh Dinamis? Untuk sekarang, Orc.
                enemy_type = 'orc'
                uid = str(uuid.uuid4())
                
                Enemy(spawn_pos, [self.camera_group, self.enemy_sprites], self.player, self.obstacle_sprites, enemy_type, self.difficulty_multiplier, uid=uid)
                
                # Broadcast
                if hasattr(self.manager, 'network_client') and self.manager.network_client:
                     self.manager.network_client.send_event('spawn_enemy', {
                         'uid': uid,
                         'type': enemy_type,
                         'pos': spawn_pos,
                         'diff': self.difficulty_multiplier
                     })
        else:
             # Spawn tersebar standar
             self.spawn_enemy()

    def get_survival_time_str(self):
        elapsed_ms = pygame.time.get_ticks() - self.survival_start_time
        seconds = (elapsed_ms // 1000) % 60
        minutes = (elapsed_ms // 60000)
        return f"{minutes:02}:{seconds:02}"

    def draw_interaction_prompt(self, surf):
        # Cek interaksi terdekat
        for sprite in self.interactable_sprites:
            dist = (self.player.pos - sprite.pos).magnitude()
            if dist < sprite.interaction_radius:
                if hasattr(sprite, 'state') and sprite.state == 'closed':
                    font = self.debug_font # Gunakan font debug atau load UI font
                    text = font.render("[E] OPEN", True, (255, 255, 255))
                    # Gambar di atas pemain
                    rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60))
                    surf.blit(text, rect)
                    return # Hanya tampilkan satu
    def handle_interaction(self):
        # Cari yang terdekat
        closest = None
        min_dist = float('inf')
        
        for sprite in self.interactable_sprites:
            dist = (self.player.pos - sprite.pos).magnitude()
            if dist < sprite.interaction_radius and dist < min_dist:
                min_dist = dist
                closest = sprite
        
        if closest:
            closest.interact(self.player)

    def draw_ui(self):
        surf = self.manager.ui_surface
        
        # Prompt Interaksi
        self.draw_interaction_prompt(surf)
        
        # 1. Health Bar
        bar_x, bar_y = 20, 20
        bar_width, bar_height = 200, 20
        # Background masih berguna untuk blending transparan
        # pygame.draw.rect(surf, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height))
        # Logika dipindah ke Shader
        
        # Outline Health Bar
        pygame.draw.rect(surf, (200, 200, 200), (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)
        
        # XP Bar
        xp_y = bar_y + 30
        pygame.draw.rect(surf, (150, 150, 150), (bar_x - 1, xp_y - 1, bar_width + 2, 10 + 2), 1)

        # Stamina Bar (Baru)
        stamina_y = xp_y + 15
        st_width = int(bar_width * (self.player.stamina / self.player.max_stamina))
        pygame.draw.rect(surf, (0, 0, 0), (bar_x, stamina_y, bar_width, 8)) # BG
        pygame.draw.rect(surf, (0, 191, 255), (bar_x, stamina_y, st_width, 8)) # Biru
        pygame.draw.rect(surf, (200, 200, 200), (bar_x - 1, stamina_y - 1, bar_width + 2, 8 + 2), 1) # Outline

        font = pygame.font.SysFont('arial', 24, bold=True)
        level_surf = font.render(f"LV. {self.player.level}", True, (255, 255, 255))
        surf.blit(level_surf, (bar_x + bar_width + 20, bar_y - 2))
        
        # Debug Overlay
        if self.manager.debug_mode:
            self.draw_debug_overlay(surf)

        # Survival Timer
        timer_str = self.get_survival_time_str()
        t_surf = font.render(timer_str, True, (255, 255, 255))
        # Draw Timer BG
        t_rect = t_surf.get_rect(center=(surf.get_width()//2, 40))
        bg_rect = t_rect.inflate(20, 10)
        pygame.draw.rect(surf, (0, 0, 0, 150), bg_rect, border_radius=5)
        surf.blit(t_surf, t_rect)

        # Minimap
        self.minimap.draw(surf)

        # Hitung Data Bar untuk Shader (UV Normalisasi)
        sw, sh = self.manager.resolution
        # Kalkulasi Y: Pygame Top=0, GL Bottom=0?
        # Logic VFlip Shader: v_text 0,0 biasanya Bottom-Left di GL kecuali dibalik.
        # Tapi VBO saya bilang (-1,1)->(0,0), jadi UV 0,0 adalah TOP-LEFT.
        # Jadi kita bisa pakai rasio langsung: y / height.
        bd = {
            'health': max(0.0, self.player.health / self.player.max_health),
            'xp': max(0.0, self.player.exp / self.player.exp_required),
            'health_rect': (20/sw, 20/sh, 200/sw, 20/sh),
            'xp_rect': (20/sw, (20+30)/sh, 200/sw, 10/sh) 
        }
        return bd

    def draw_debug_overlay(self, surf):
        fps = int(self.manager.clock.get_fps())
        sprites_total = len(self.camera_group)
        sprites_visible = len([s for s in self.camera_group.sprites() if self.camera_group.virtual_surface.get_rect().colliderect(s.rect.move(-self.camera_group.offset.x, -self.camera_group.offset.y))])

        # Entity Breakdown
        enemies = len(self.enemy_sprites)
        remotes = len(self.remote_players)
        vfx = sprites_total - enemies - remotes - 1 # -1 for player
        
        # Mouse World Pos
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        # Convert screen to world: screen_pos + camera_offset
        # Note: mouse_pos is relative to actual window, we need to map to virtual surface if scaled
        # But here manager.resolution and virtual_surface usually match or are handled by main.py
        world_mouse = mouse_pos + self.camera_group.offset
        cx, cy = self.chunk_manager.get_chunk_coord(self.player.pos)
        
        info_lines = [
            f"FPS: {fps} | DT: {self.manager.clock.get_time()}ms",
            f"Entities: {sprites_total} (Vis: ~{sprites_visible})",
            f"  - Enemies: {enemies} | Remote: {remotes} | VFX: {vfx}",
            f"Player Pos: ({int(self.player.pos.x)}, {int(self.player.pos.y)})",
            f"Chunk: {cx}, {cy} | Queue: {len(self.chunk_manager.load_queue)}",
            f"Difficulty: {self.difficulty_multiplier:.2f} | Mouse: ({int(world_mouse.x)}, {int(world_mouse.y)})",
            f"Hit Stop: {self.manager.is_hit_stopped}"
        ]
        
        y = 60
        for line in info_lines:
            text = self.debug_font.render(line, True, (255, 255, 0))
            pygame.draw.rect(surf, (0, 0, 0, 150), (10, y, text.get_width()+10, 20))
            surf.blit(text, (15, y))
            y += 22


    def draw(self):
        # Bersihkan Surface UI (Penting!)
        self.manager.ui_surface.fill((0, 0, 0, 0))
        
        # Deteksi perubahan surface dan update kamera
        if self.virtual_surface != self.manager.render_surface:
            print(f"Surface Resize Detected: {self.manager.render_surface.get_size()}")
            self.virtual_surface = self.manager.render_surface
            self.virtual_width, self.virtual_height = self.virtual_surface.get_size()
            self.camera_group.resize(self.virtual_surface)
        
        # FAILSAFE: Paksa HW/HH setiap frame untuk debug "Kiri Atas"
        # Jika ini memperbaiki, berarti init rusak.
        self.camera_group.half_width = self.virtual_width // 2
        self.camera_group.half_height = self.virtual_height // 2
        
        self.virtual_surface.fill((30, 30, 45))
        self.camera_group.custom_draw()
        
        # Gambar HUD dan Menu ke layer terpisah
        bar_data = self.draw_ui()
        
        if self.paused:
            if self.level_up_active:
                self.draw_level_up_menu()
            else:
                self.draw_pause_menu()
            
        return bar_data

    def draw_level_up_menu(self):
        surf = self.manager.ui_surface
        sw, sh = self.manager.resolution
        
        # 1. Overlay
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))
        
        # 2. Judul
        title = self.debug_font.render("LEVEL UP!", True, (255, 215, 0))
        # Scale up
        title = pygame.transform.scale(title, (int(title.get_width()*4), int(title.get_height()*4)))
        t_rect = title.get_rect(center=(sw//2, 100))
        surf.blit(title, t_rect)
        
        # 3. Kartu
        card_w, card_h = 250, 350
        gap = 40
        total_w = 3 * card_w + 2 * gap
        start_x = (sw - total_w) // 2
        cls_y = (sh - card_h) // 2
        
        mouse_pos = pygame.mouse.get_pos()
        
        font_name = pygame.font.SysFont('arial', 28, bold=True)
        font_desc = pygame.font.SysFont('arial', 20)
        
        for i, opt in enumerate(self.upgrade_options):
            x = start_x + i*(card_w+gap)
            rect = pygame.Rect(x, cls_y, card_w, card_h)
            
            # Hover
            is_hover = rect.collidepoint(mouse_pos)
            color = (30, 30, 50) if not is_hover else (50, 50, 80)
            border = (100, 100, 200) if not is_hover else (255, 215, 0)
            
            pygame.draw.rect(surf, color, rect, border_radius=15)
            pygame.draw.rect(surf, border, rect, 3, border_radius=15)
            
            # Text (NAMA)
            name_surf = font_name.render(opt['name'], True, (255, 255, 255))
            surf.blit(name_surf, name_surf.get_rect(center=(x+card_w//2, cls_y + 60)))
            
            # Wrapping Text untuk Deskripsi
            words = opt['description'].split(' ')
            lines = []
            curr_line = words[0]
            for word in words[1:]:
                if font_desc.size(curr_line + ' ' + word)[0] < card_w - 40:
                    curr_line += ' ' + word
                else:
                    lines.append(curr_line)
                    curr_line = word
            lines.append(curr_line)
            
            desc_y = cls_y + 110
            for line in lines:
                line_surf = font_desc.render(line, True, (200, 200, 200)) # Removed kwarg
                surf.blit(line_surf, line_surf.get_rect(center=(x+card_w//2, desc_y)))
                desc_y += 24
            
            # Petunjuk Tombol
            hint_surf = font_desc.render(f"Tekan [{i+1}]", True, (100, 100, 100))
            surf.blit(hint_surf, hint_surf.get_rect(center=(x+card_w//2, cls_y + 320)))

    def draw_pause_menu(self):
        surf = self.manager.ui_surface
        # 1. Overlay Redup
        overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))
        
        # 2. Judul
        font_t = pygame.font.SysFont('arial', 60, bold=True)
        title_surf = font_t.render("PAUSED", True, (255, 255, 255))
        title_rect = title_surf.get_rect(center=(surf.get_width()//2, 150))
        surf.blit(title_surf, title_rect)
        
        # 3. Opsi
        font_o = pygame.font.SysFont('arial', 32)
        start_y = 300
        mouse_pos = pygame.mouse.get_pos()
        sw = surf.get_width()
        
        for i, option in enumerate(self.menu_options):
            # Area Deteksi Hover (Tetap di tengah)
            detect_rect = pygame.Rect(0, 0, 400, 50)
            detect_rect.center = (sw // 2, start_y + i * 60)
            
            if detect_rect.collidepoint(mouse_pos):
                self.menu_index = i
                
            color = (100, 255, 218) if i == self.menu_index else (255, 255, 255)
            text = f"> {option} <" if i == self.menu_index else option
            opt_surf = font_o.render(text, True, color)
            rect = opt_surf.get_rect(center=(sw//2, start_y + i * 60))
            surf.blit(opt_surf, rect)
