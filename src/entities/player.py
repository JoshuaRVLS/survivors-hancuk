
import pygame
import os
import math
from .entity import Entity
from ..settings import *
from ..utils import load_sprite_sheet
from ..vfx import GhostSprite, WalkParticle, SlashEffect
from ..core.input import InputManager

class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites, enemy_sprites, char_type='adventurer'):
        super().__init__(pos, groups)
        self.char_config = CHARACTER_DATA.get(char_type, CHARACTER_DATA['adventurer'])
        self.obstacle_sprites = obstacle_sprites
        self.enemy_sprites = enemy_sprites
        
        # Stats dari config
        self.health = self.char_config['health']
        self.max_health = self.char_config['health']
        self.speed = self.char_config['speed']
        
        # Sistem Senjata
        # Kita simpan data senjata (dict) di inventory terpisah
        self.weapons = {}
        
        # Inisialisasi Senjata Awal
        start_weapon = self.char_config.get('starting_weapon', 'sword')
        # Deep copy agar upgrade tidak bentrok antar pemain
        self.weapons[start_weapon] = WEAPON_DATA.get(start_weapon).copy()
        self.weapons[start_weapon]['last_attack_time'] = 0
        
        # Pointer ke senjata 'Utama' untuk serangan biasa
        self.main_weapon_id = start_weapon
        
        # State Aura
        self.aura_tick_timer = 0
        self.aura_sprite = None
        
        # Ambil instance game global untuk akses efisien
        import __main__
        self.game = getattr(__main__, 'game', None)
        
        self.import_assets()
        self.facing_direction = 'down'
        self.status = 'idle'
        self.image = self.animations['idle_down'][0]
        self.rect = self.image.get_rect(center=pos)
        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        # Hitbox (Diratakan di kaki)
        # Sesuaikan Hitbox untuk Karakter Wanita (Lebih kecil/ramping)
        if 'female' in self.char_config['name'].lower():
            # Hitbox lebih ketat untuk menghindar lebih baik
            self.hitbox = self.rect.inflate(-20, -26)
            self.hitbox_offset_y = 6 # Sesuaikan posisi kaki
        else:
            # Fisika Adventurer Default - Hitbox lebih kecil untuk presisi
            self.hitbox = self.rect.inflate(-40, -44)
            self.hitbox_offset_y = 12
        self._sync_hitbox_with_pos()
        
        # Timer
        self.is_dashing = False
        self.dash_time = 0
        self.dash_cooldown_time = 0
        self.dash_direction = pygame.math.Vector2()
        self.attack_hitbox = None
        self.attack_cooldown_timer = 0
        self.ghost_timer = 0
        self.walk_particle_timer = 0
        
        # Stamina
        self.stamina = 100
        self.max_stamina = 100
        self.stamina_regen = 30
        
        # XP
        self.level = 1
        self.exp = 0
        self.exp_required = 100
        self.lifesteal = 0.0 # Percentage of damage returned as health

    def import_assets(self):
        base_path = self.char_config['asset_path']
        scale = 2.5
        char_name = self.char_config['name'].lower()
        self.animations = {}

        if 'female' in char_name:
            # Struktur karakter wanita (48x64, nama spesifik)
            width, height = self.char_config.get('frame_size', (48, 64))
            # Petakan suffix asset wanita ke arah status pemain internal
            dirs_map = {
                'Down': 'down',
                'Up': 'up',
                'Left_Down': 'left',
                'Right_Down': 'right'
            }
            
            # Gunakan folder animasi khusus
            anim_folders = [('Idle', 'idle'), ('Walk', 'run'), ('Dash', 'dash'), ('Death', 'death')]
            
            for folder, key in anim_folders:
                for f_suffix, status_dir in dirs_map.items():
                    # Coba berbagai pola nama file untuk atasi inkonsistensi
                    # misal Idle/Idle_Down.png vs Walk/walk_Down.png
                    patterns = [
                        f"{folder}_{f_suffix}.png",
                        f"{folder.lower()}_{f_suffix}.png",
                        f"{folder}_{f_suffix.lower()}.png",
                        f"{folder.lower()}_{f_suffix.lower()}.png"
                    ]
                    
                    found_path = None
                    for filename in patterns:
                        test_path = os.path.join(base_path, folder, filename)
                        if os.path.exists(test_path):
                            found_path = test_path
                            break
                    
                    if found_path:
                        frames = load_sprite_sheet(found_path, width, height, scale=scale, trim=True)
                        if frames:
                            # Petakan ke status seperti 'idle_down', 'run_right'
                            self.animations[f'{key}_{status_dir}'] = frames
                            # Fallback generik untuk kematian
                            if key == 'death' and status_dir == 'down':
                                self.animations['death'] = frames

            # 3. Fallback untuk state yang hilang (Serang, Luka)
            all_dirs = ['down', 'up', 'left', 'right']
            for d in all_dirs:
                # Petakan serang ke lari (belum ada animasi serang khusus wanita)
                if f'attack_{d}' not in self.animations:
                    self.animations[f'attack_{d}'] = self.animations.get(f'run_{d}', self.animations.get(f'idle_{d}', []))
                # Petakan luka ke idle
                if f'hurt_{d}' not in self.animations:
                    self.animations[f'hurt_{d}'] = self.animations.get(f'idle_{d}', [])
                # Pastikan death generik ada
                if 'death' not in self.animations:
                    self.animations['death'] = self.animations.get('idle_down', [])

        else:
            # Struktur Adventurer Default (96x80)
            dirs = ['down', 'up', 'left', 'right']
            for d in dirs:
                self.animations[f'idle_{d}'] = load_sprite_sheet(os.path.join(base_path, "IDLE", f"idle_{d}.png"), 96, 80, scale=scale, trim=True)
                self.animations[f'run_{d}'] = load_sprite_sheet(os.path.join(base_path, "RUN", f"run_{d}.png"), 96, 80, scale=scale, trim=True)
                self.animations[f'attack_{d}'] = load_sprite_sheet(os.path.join(base_path, "ATTACK 1", f"attack1_{d}.png"), 96, 80, scale=scale, trim=True)
                self.animations[f'hurt_{d}'] = self.animations[f'idle_{d}']
                self.animations['death'] = self.animations[f'idle_down']
        

    def input(self):
        current_time = pygame.time.get_ticks()
        self.direction = InputManager.get_movement_vector()
        
        if self.direction.magnitude() > 0:
            if abs(self.direction.x) > abs(self.direction.y):
                self.facing_direction = 'right' if self.direction.x > 0 else 'left'
            else:
                self.facing_direction = 'down' if self.direction.y > 0 else 'up'

        # Cek Setting Auto-Attack
        auto_attack = getattr(self.game.active_scene, 'auto_attack', True)

        if not auto_attack:
            # Manual Aiming & Attack
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            rel_pos = mouse_pos - pygame.math.Vector2(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)
            aim_angle = 0
            if rel_pos.magnitude() > 0:
                aim_angle = rel_pos.as_polar()[1]

            if InputManager.is_action_pressed('ATTACK'):
                # Serangan manual pakai SENJATA UTAMA
                # Cek cooldown khusus senjata utama
                w_data = self.weapons[self.main_weapon_id]
                last_time = w_data.get('last_attack_time', 0)
                
                if current_time - last_time > w_data['cooldown']:
                    if not self.status.startswith('death') and not self.is_hurting:
                        self.attack(self.main_weapon_id, aim_angle)
                        w_data['last_attack_time'] = current_time

        # Dash (Pakai Stamina)
        DASH_COST = 40
        if InputManager.is_action_pressed('DASH') and not self.is_dashing and current_time - self.dash_cooldown_time > DASH_COOLDOWN:
            if self.stamina >= DASH_COST:
                self.stamina -= DASH_COST
                self.is_dashing = True
                self.dash_time = current_time
                self.dash_cooldown_time = current_time
                self.dash_direction = self.direction.copy() if self.direction.magnitude() > 0 else self._get_facing_direction_vec()

    def auto_attack_logic(self):
        current_time = pygame.time.get_ticks()
        
        # Cek Setting
        if not getattr(self.game.active_scene, 'auto_attack', True):
            return

        # Iterasi SEMUA senjata
        for w_id, w_data in self.weapons.items():
            if w_id == 'aura': continue # Pasif
            
            # Cek Cooldown
            last_time = w_data.get('last_attack_time', 0)
            if current_time - last_time < w_data['cooldown']:
                continue
            
            # Smart Targeting
            if not self.enemy_sprites:
                continue

            # Filter musuh valid
            candidates = [e for e in self.enemy_sprites if not (hasattr(e, 'is_dead') and e.is_dead)]
            
            # Urutkan berdasarkan jarak
            player_center = pygame.math.Vector2(self.hitbox.center)
            MAX_AUTO_AIM_RANGE = w_data.get('range', 500) if w_id == 'fireball' else 500
            
            valid_targets = []
            for enemy in candidates:
                dist = player_center.distance_to(pygame.math.Vector2(enemy.hitbox.center))
                if dist < MAX_AUTO_AIM_RANGE:
                    valid_targets.append((dist, enemy))
            
            if not valid_targets:
                continue
                
            valid_targets.sort(key=lambda x: x[0]) # Ascending
            sorted_enemies = [x[1] for x in valid_targets]
            
            # Logika Serang
            proj_count = w_data.get('projectile_count', 1)
            
            if proj_count > 1:
                shots_to_fire = min(proj_count, len(sorted_enemies))
                target_angles = []
                for i in range(shots_to_fire):
                    target = sorted_enemies[i]
                    aim_vec = pygame.math.Vector2(target.hitbox.center) - player_center
                    angle = aim_vec.as_polar()[1]
                    target_angles.append(angle)
                
                # Update hadap hanya untuk senjata utama
                if w_id == self.main_weapon_id:
                     closest_enemy = sorted_enemies[0]
                     aim_vec = pygame.math.Vector2(closest_enemy.hitbox.center) - player_center
                     face_angle = aim_vec.as_polar()[1]
                     self._update_facing(face_angle)

                if not self.status.startswith('death'): # Boleh tembak sambil gerak/luka
                    self.attack(w_id, target_angles=target_angles)
                    w_data['last_attack_time'] = current_time
                    
            else:
                # Single Target
                closest_enemy = sorted_enemies[0]
                aim_vec = pygame.math.Vector2(closest_enemy.hitbox.center) - player_center
                angle = aim_vec.as_polar()[1]
                
                if w_id == self.main_weapon_id:
                    self._update_facing(angle)
                
                if not self.status.startswith('death'):
                    self.attack(w_id, main_angle=angle)
                    w_data['last_attack_time'] = current_time

    def _update_facing(self, angle):
        if -45 <= angle < 45: self.facing_direction = 'right'
        elif 45 <= angle < 135: self.facing_direction = 'down'
        elif -135 <= angle < -45: self.facing_direction = 'up'
        else: self.facing_direction = 'left'

    def _get_facing_direction_vec(self):
        vecs = {'right': (1,0), 'left': (-1,0), 'up': (0,-1), 'down': (0,1)}
        return pygame.math.Vector2(vecs.get(self.facing_direction, (0,1)))

    def attack(self, weapon_id, main_angle=0, target_angles=None):
        # Ambil Data
        w_data = self.weapons.get(weapon_id, {})
        
        angles = []
        if target_angles:
            angles = target_angles
        else:
            count = w_data.get('projectile_count', 1)
            if count == 1:
                angles = [main_angle]
            else:
                spread = 30
                step = spread / (count - 1) if count > 1 else 0
                start = main_angle - (spread/2)
                for i in range(count):
                    angles.append(start + i * step)

        # Logika Fireball
        if weapon_id == 'fireball':
            from ..vfx import Fireball
            groups = [self.groups()[0]]
            if self.game: groups.append(self.game.active_scene.light_sprites)
            
            for shot_angle in angles:
                 rad = math.radians(shot_angle)
                 dir_vec = pygame.math.Vector2(math.cos(rad), math.sin(rad))
                 # Kirim stats
                 Fireball(self.rect.center, groups, dir_vec, self, self.obstacle_sprites, self.enemy_sprites, damage=w_data['damage'], speed=w_data['speed'])
                 Fireball(self.rect.center, groups, dir_vec, self, self.obstacle_sprites, self.enemy_sprites, damage=w_data['damage'], speed=w_data['speed'])
            
            if self.game and hasattr(self.game, 'network_client') and self.game.network_client:
                 self.game.network_client.send_event('attack', {'weapon': weapon_id, 'angles': angles})
            return

        # Slash Standar (Sword/Default)
        range_val = w_data.get('range', 100)
        self.attack_hitboxes = []
        
        for shot_angle in angles:
            # Hitung Posisi Hitbox berdasarkan sudut
            # Offset dinamis berdasarkan range
            rad = math.radians(shot_angle)
            offset_dist = range_val * 0.4
            offset = pygame.math.Vector2(math.cos(rad) * offset_dist, math.sin(rad) * offset_dist)
            
            center_pos = pygame.math.Vector2(self.hitbox.center) + offset
            
            # Ukuran Hitbox Dinamis
            size = int(range_val * 0.8)
            rect = pygame.Rect(0, 0, size, size)
            rect.center = center_pos
            self.attack_hitboxes.append(rect)
            
            groups = self.groups()
            if self.game:
                groups.append(self.game.active_scene.light_sprites)
            
            # Tentukan warna
            color = w_data.get('slash_color', (255, 255, 255))
            SlashEffect(self.hitbox.center + offset, groups, shot_angle, self, scale=range_val/120.0, color=color)

        if self.game and hasattr(self.game, 'network_client') and self.game.network_client:
             self.game.network_client.send_event('attack', {'weapon': weapon_id, 'angles': angles})

        self.attack_active_time = pygame.time.get_ticks() 

    def update_aura(self):
        if 'aura' not in self.weapons:
            return
            
        data = self.weapons['aura']
        current_time = pygame.time.get_ticks()
        
        if current_time - self.aura_tick_timer > data['cooldown']:
            # Logika Tick
            targets = [e for e in self.enemy_sprites if not (hasattr(e, 'is_dead') and e.is_dead)]
            radius = data['range']
            damage = data['damage']
            
            hit_any = False
            player_center = pygame.math.Vector2(self.hitbox.center)
            for enemy in targets:
                # Fix: Pastikan musuh punya hitbox
                if not hasattr(enemy, 'hitbox'): continue
                
                enemy_center = pygame.math.Vector2(enemy.hitbox.center)
                dist = player_center.distance_to(enemy_center)
                
                if dist < radius:
                    if hasattr(enemy, 'health'):
                        enemy.health -= damage
                        enemy.is_hurting = True
                        enemy.hurt_time = current_time
                        
                        # Tambah Visual Spark
                        from ..vfx import HitSpark
                        visual_groups = [g for g in self.groups() if hasattr(g, 'custom_draw')]
                        if not visual_groups and self.groups(): visual_groups = [self.groups()[0]]
                        HitSpark(enemy.hitbox.center, visual_groups)
                        
                        hit_any = True
                
            self.aura_tick_timer = current_time

        # Visual
        from ..vfx.aura import AuraSprite
        if self.aura_sprite is None:
             # Spawn visual
             groups = [self.groups()[0]] # Camera Group
             self.aura_sprite = AuraSprite(groups, self, data['range'], data.get('color', (255, 215, 0, 50)))
        else:
             self.aura_sprite.set_radius(data['range'])

    @property
    def weapon_data(self):
        # Kompatibilitas mundur untuk kode lama
        return self.weapons.get(self.main_weapon_id, {})
    
    @property
    def damage(self):
         return self.weapon_data.get('damage', 10) 

    def apply_knockback(self, dt):
        if self.knockback_vector.magnitude() > 0.1:
            self._apply_velocity_with_collision(self.knockback_vector * dt * 60, self.obstacle_sprites, self.enemy_sprites)
            self.knockback_vector *= pow(0.8, dt * 60)
        else:
            self.knockback_vector = pygame.math.Vector2()

    def update(self, dt):
        current_time = pygame.time.get_ticks()
        
        # Regen Stamina
        if not self.is_dashing:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen * dt)
            
        self.input()
        self.auto_attack_logic() # Trigger Auto-Aim
        self.update_aura()       # Trigger Pasif
        self.get_status()
        self.move(self.speed, dt)
        self.apply_knockback(dt)
        self.animate(dt)
        self._sync_visuals()
        
        # Visual Premium: Ghost Trail saat dash
        if self.is_dashing:
            # Cek durasi dash
            if current_time - self.dash_time > DASH_DURATION:
                self.is_dashing = False
            
            self.ghost_timer += dt * 1000
            if self.ghost_timer > 30: # tiap 30ms
                GhostSprite(self.rect.topleft, self.image, self.groups())
                self.ghost_timer = 0
                
        if self.direction.magnitude() > 0 and not self.is_dashing:
            self.walk_particle_timer += dt * 1000
            if self.walk_particle_timer > 100: # tiap 100ms
                WalkParticle(self.hitbox.center, self.groups())
                self.walk_particle_timer = 0
                
        # Hapus hitbox serangan setelah durasi singkat (150ms)
        if hasattr(self, 'attack_hitboxes') and self.attack_hitboxes:
            last_hit_time = getattr(self, 'attack_active_time', 0)
            if current_time - last_hit_time > 150:
                self.attack_hitboxes = []
            
        # Kedipan Luka
        if self.is_hurting:
            alpha = 100 if (pygame.time.get_ticks() // 50) % 2 == 0 else 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def get_status(self):
        # 1. Cek Pemulihan Luka
        if self.is_hurting and pygame.time.get_ticks() - self.hurt_time > 300:
            self.is_hurting = False

        # 2. Cegah status gerak menimpa animasi aktif
        if self.is_dead:
            self.status = 'death'
            return
        if self.status.startswith('attack'):
            return
        if self.is_hurting:
            self.status = f'hurt_{self.facing_direction}'
            return

        base = 'idle'
        if self.direction.magnitude() > 0: base = 'run'
        
        self.status = f"{base}_{self.facing_direction}"

    def move(self, speed, dt):
        vel = self.dash_direction * DASH_SPEED * dt * 60 if self.is_dashing else self.direction * speed * dt * 60
        self._apply_velocity_with_collision(vel, self.obstacle_sprites, self.enemy_sprites)

    def collision(self, direction, vel, obstacle_sprites, enemy_sprites=None):
        # OPTIMASI: Filter rintangan terdekat
        # Gunakan rect kasar untuk fase broad
        broad_rect = self.hitbox.inflate(20, 20)
        dummy = pygame.sprite.Sprite()
        dummy.rect = broad_rect
        
        # Ambil kandidat (C-optimized)
        nearby_obstacles = pygame.sprite.spritecollide(dummy, obstacle_sprites, False)
        
        targets = list(nearby_obstacles)
        
        # Hanya tabrak musuh jika TIDAK dashing (Phasing)
        if enemy_sprites and not self.is_dashing:
            # Filter musuh juga? Biasanya lebih sedikit dari rintangan
            nearby_enemies = pygame.sprite.spritecollide(dummy, enemy_sprites, False)
            targets += [e for e in nearby_enemies if hasattr(e, 'is_dead') and not e.is_dead]
        
        for sprite in targets:
            target_hitbox = getattr(sprite, 'hitbox', sprite.rect)
            if target_hitbox.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if vel > 0: self.hitbox.right = target_hitbox.left
                    else: self.hitbox.left = target_hitbox.right
                else:
                    if vel > 0: self.hitbox.bottom = target_hitbox.top
                    else: self.hitbox.top = target_hitbox.bottom
                self._sync_pos_with_hitbox()

    def _sync_pos_with_hitbox(self):
        super()._sync_pos_with_hitbox()

    def _sync_visuals(self):
        self.rect.centerx = self.hitbox.centerx
        self.rect.bottom = self.hitbox.bottom

    def take_damage(self, amount, source_pos=None):
        if self.is_dead or self.is_hurting: return
        
        self.health -= amount
        self.is_hurting = True
        self.hurt_time = pygame.time.get_ticks()
        self.status = f'hurt_{self.facing_direction}'
        self.frame_index = 0
        
        # Terapkan knockback
        if source_pos:
            kb_dir = self.pos - pygame.math.Vector2(source_pos)
            if kb_dir.magnitude() > 0:
                self.knockback_vector = kb_dir.normalize() * 15

        if self.health <= 0:
            self.is_dead = True
            self.status = 'death' # Fallback ke death generik di entity.animate

    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= self.exp_required:
            self.level += 1
            self.exp -= self.exp_required
            self.exp_required = int(self.exp_required * 1.5)
            # Trigger UI Level Up
            if self.game and hasattr(self.game.active_scene, 'trigger_level_up'):
                self.game.active_scene.trigger_level_up()
