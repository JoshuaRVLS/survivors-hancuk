
import pygame
import os
import random
from ..settings import *
from ..utils import load_sprite_sheet
from ..core.collision import SAT
from ..vfx import DeathEffect, HitSpark
from ..items import ExperienceGem
from .interactables import HealthPotion
from .entity import Entity

class Enemy(Entity):
    def __init__(self, pos, groups, player, obstacle_sprites, enemy_type='orc', difficulty=1.0, uid=None):
        self.enemy_type = enemy_type # Set this BEFORE super().__init__ so _load_custom_hitbox works
        super().__init__(pos, groups)
        self.player = player
        self.uid = uid # ID Network
        self.obstacle_sprites = obstacle_sprites
        self.data = ENEMY_DATA.get(enemy_type, ENEMY_DATA['orc'])
        
        # Statistik
        self.difficulty = difficulty
        self.health = self.data['health'] * self.difficulty
        self.speed = self.data['speed'] * (1.0 + (self.difficulty - 1.0) * 0.3)
        self.damage = self.data['damage'] * self.difficulty
        
        # Ambil instance game global
        import __main__
        self.game = getattr(__main__, 'game', None)
        
        self.import_assets()
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect(topleft=pos)
        self.pos = pygame.math.Vector2(self.rect.topleft)
        
        # Hitbox
        self.hitbox = self.rect.copy()
        if self.enemy_type.startswith('orc'):
            # Hitbox khusus Orc - pas di kaki
            self.hitbox.height = 20
            self.hitbox.width = self.rect.width * 0.4
            self.hitbox_offset_y = 15 # Posisi dekat kaki
        else:
            self.hitbox.height = 15
            self.hitbox.width = self.rect.width * 0.7
            self.hitbox_offset_y = 0 
        
        self.hitbox.center = self.rect.center
        self.hitbox.y += self.hitbox_offset_y
        
        self.facing_right = True
        
        # Timer
        self.attack_cooldown = 1500 # ms
        self.last_attack_time = 0
        
        # Deteksi Stuck
        self.last_pos = pygame.math.Vector2(self.pos)
        self.stuck_timer = 0
        self.stuck_boost = pygame.math.Vector2()
        
        # Visual States
        self.is_flashing = False
        self.flash_time = 0

    def import_assets(self):
        base_path = self.data['asset_path']
        scale = self.data.get('scale', 2.0)
        self.animations = {'idle': [], 'walk': [], 'attack': [], 'hurt': [], 'death': []}
        
        # Menggunakan pola nama file
        if self.enemy_type.startswith('orc'):
            self.animations['idle'] = load_sprite_sheet(os.path.join(base_path, "Orc-Idle.png"), 100, 100, scale=scale, trim=True)
            self.animations['walk'] = load_sprite_sheet(os.path.join(base_path, "Orc-Walk.png"), 100, 100, scale=scale, trim=True)
            self.animations['attack'] = load_sprite_sheet(os.path.join(base_path, "Orc-Attack01.png"), 100, 100, scale=scale, trim=True)
            self.animations['hurt'] = load_sprite_sheet(os.path.join(base_path, "Orc-Hurt.png"), 100, 100, scale=scale, trim=True)
            self.animations['death'] = load_sprite_sheet(os.path.join(base_path, "Orc-Death.png"), 100, 100, scale=scale, trim=True)

    def get_status(self):
        # Prioritas 1: Mati
        if self.health <= 0:
            self.status = 'death'
            self.is_dead = True
            return

        # Prioritas 2: Kena Hit (Stun)
        if self.is_hurting:
            self.status = 'hurt'
            # Durasi stun
            if pygame.time.get_ticks() - self.hurt_time > 400:
                self.is_hurting = False
            return
            
        # Prioritas 3: Serang (Kunci animasi)
        # Entity.animate akan mereset status ke 'idle' saat selesai
        if self.status == 'attack':
            return

        # Prioritas 4: Gerak
        if self.direction.magnitude() > 0:
            self.status = 'walk'
        else:
            self.status = 'idle'

    def update(self, dt):
        # Optimasi Jarak
        dist_sq = (self.player.pos - self.pos).length_squared()
        
        # Despawn jika terlalu jauh (misal 5000px) untuk jaga performa
        # 5000^2 = 25,000,000
        if dist_sq > 25000000:
            self.kill()
            return

        if dist_sq > 9000000: # 3000px
            self.apply_knockback(dt) # Tetap proses fisika jika didorong
            return

        if self.is_dead:
            if self.frame_index < len(self.animations['death']) - 1:
                self.animate(dt)
            else:
                if not hasattr(self, 'dropped_items'):
                    # Fix: Filter untuk CameraGroup (Group standar tidak punya custom_draw)
                    visual_groups = [g for g in self.groups() if hasattr(g, 'custom_draw')]
                    if not visual_groups and self.groups(): visual_groups = [self.groups()[0]]
                    DeathEffect(self.rect.center, visual_groups)
                    for _ in range(3): ExperienceGem(self.rect.center, visual_groups, self.player)
                    for _ in range(3): ExperienceGem(self.rect.center, visual_groups, self.player)
                    
                    # Drop Health Potion (10% chance)
                    if random.random() < 0.10:
                        HealthPotion(self.rect.center, visual_groups, self.player)
                    
                    self.dropped_items = True
                    
                    # Beri tahu Network (Jika Host)
                    if self.game and hasattr(self.game, 'network_client') and self.game.network_client:
                         # Kita broadcast kill hanya jika kita authority (Host)
                         if self.game.network_client.is_host:
                             self.game.network_client.send_event('kill_enemy', {'uid': self.uid})
                    
                    self.kill()
        else:
            self.get_status()
            self.check_player_attacks()
            self.ai_logic(dt)
            self.animate(dt)
            
            # Flip Visual Sederhana
            if self.direction.x > 0: self.facing_right = True
            elif self.direction.x < 0: self.facing_right = False
            
        # Flip gambar jika perlu
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
            
        # Terapkan knockback selalu
        self.apply_knockback(dt)
            
        # Efek Berkedip saat Kena Damage (Hurt atau Flash dari Aura)
        if self.is_hurting or self.is_flashing:
            if (pygame.time.get_ticks() // 50) % 2 == 0:
                # Blink (buat transparan)
                self.image = self.image.copy()
                self.image.set_alpha(0)
            
            # Reset flash state after 150ms
            if self.is_flashing and pygame.time.get_ticks() - self.flash_time > 150:
                self.is_flashing = False

    def ai_logic(self, dt):
        # Kunci Prioritas: Jika menyerang, jangan update gerakan
        if self.status == 'attack':
            self.direction = pygame.math.Vector2()
            self.apply_knockback(dt)
            return

        # 1. Kejar Pemain
        # CARI TARGET TERDEKAT (Lokal atau Remote)
        target = self.player
        min_dist_sq = (self.player.pos - self.pos).length_squared()
        
        if self.game and hasattr(self.game.active_scene, 'remote_players'):
            for rp in self.game.active_scene.remote_players:
                d_sq = (rp.pos - self.pos).length_squared()
                if d_sq < min_dist_sq:
                    min_dist_sq = d_sq
                    target = rp

        direction = target.pos - self.pos
        distance = direction.magnitude()
        
        # Kejar dasar
        if distance < self.data['chase_range']:
            if distance > self.data['attack_range'] * 0.8:
                self.direction = direction.normalize()
            else:
                self.direction = pygame.math.Vector2()
                # 2. Logika Serang
                self.attack_player(target) # Oper target
        else:
            self.direction = pygame.math.Vector2()

        # 3. Separasi (Hindari Penumpukan)
        separation = self.get_separation_vector()
        
        # 5. Deteksi Stuck (Dorongan ekstra)
        current_pos = pygame.math.Vector2(self.pos)
        if (current_pos - self.last_pos).length_squared() < 0.2 and self.direction.magnitude() > 0:
            self.stuck_timer += dt
        else:
            self.stuck_timer = 0
            self.stuck_boost = pygame.math.Vector2()
        self.last_pos = current_pos
        
        # Jika stuck, tambahkan dorongan acak
        stuck_nudge = pygame.math.Vector2()
        if self.stuck_timer > 0.4: 
            if self.stuck_boost.magnitude() == 0:
                self.stuck_boost = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                if self.stuck_boost.magnitude() > 0: self.stuck_boost = self.stuck_boost.normalize()
            stuck_nudge = self.stuck_boost * 3.0
        
        # 4. Hindari Rintangan (Pathing Lebih Cerdas)
        avoidance = stuck_nudge
        # Cari rintangan terdekat - DIOPTIMALKAN dengan spritecollide
        # Buat rect sensor di sekitar kita
        sensor_size = 200
        sensor_rect = pygame.Rect(0, 0, sensor_size, sensor_size)
        sensor_rect.center = self.rect.center
        
        # Gunakan dummy sprite untuk cek collision
        sensor_sprite = pygame.sprite.Sprite()
        sensor_sprite.rect = sensor_rect
        
        # Ambil hanya rintangan terdekat
        nearby_obstacles = pygame.sprite.spritecollide(sensor_sprite, self.obstacle_sprites, False)
        
        closest_obstacle = None
        min_dist = 110 # Sedikit lebih besar dari cek proximity kita
        
        for obstacle in nearby_obstacles:
            # Cek radius kecil di sekitar kita
            dist = pygame.math.Vector2(self.rect.center).distance_to(obstacle.rect.center)
            if dist < min_dist:
                min_dist = dist
                closest_obstacle = obstacle

        if closest_obstacle:
            # Look-ahead: Apakah kita akan menabrak jika lurus?
            look_ahead = self.direction * 40 # preoyeksi 40px
            if look_ahead.magnitude() > 0:
                detect_rect = self.hitbox.copy()
                detect_rect.center += look_ahead
                
                target_hit = getattr(closest_obstacle, 'hitbox', closest_obstacle.rect)
                if detect_rect.colliderect(target_hit):
                    # HITUNG GESER/TANGENT
                    # Vektor dari pusat rintangan ke kita
                    to_us = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(closest_obstacle.rect.center)
                    if to_us.magnitude() > 0:
                        # 1. Dorong Jauh (Dari pusat)
                        push = to_us.normalize()
                        
                        # 2. Steering Tangent (Menyusuri sisi)
                        # Putar vektor push 90 derajat untuk dapat tangent
                        tangent = pygame.math.Vector2(-push.y, push.x)
                        
                        # Pilih arah tangent yang lebih dekat ke arah tujuan kita
                        if tangent.dot(self.direction) < (-tangent).dot(self.direction):
                            tangent = -tangent
                            
                        # Campur Push dan Tangent untuk "kurva" halus mengelilingi objek
                        avoidance = (push * 0.4 + tangent * 0.8)

        # Campur semua perilaku
        # Kejar (bobot 1.0) + Separasi (bobot 2.0) + Avoidance (bobot disesuaikan)
        final_dir = self.direction
        if separation.magnitude() > 0:
            final_dir += separation * 2.0
            
        if avoidance.magnitude() > 0:
            # Jika terblokir, kurangi niat kejar dan prioritaskan kurva
            final_dir = (self.direction * 0.4) + (avoidance * 4.0)
            
        if final_dir.magnitude() > 0:
             final_dir = final_dir.normalize()
            
        self._apply_velocity_with_collision(final_dir * self.speed * dt * 60, self.obstacle_sprites)
        self.apply_knockback(dt)

    def get_separation_vector(self):
        separation = pygame.math.Vector2()
        if not self.groups(): return separation
        
        neighbors = []
        if self.game and hasattr(self.game.active_scene, 'enemy_sprites'):
             # Limit neighbor checks for performance and stability
             all_neighbors = self.game.active_scene.enemy_sprites.sprites()
             neighbors = random.sample(all_neighbors, min(len(all_neighbors), 16))
        else:
             return separation
             
        count = 0
        separation_radius = 50 
        
        my_center = self.hitbox.center
        my_vec = pygame.math.Vector2(my_center)
        
        for enemy in neighbors:
            if enemy is self or not hasattr(enemy, 'hitbox'): continue
    
            if abs(enemy.rect.centerx - self.rect.centerx) > separation_radius: continue
            if abs(enemy.rect.centery - self.rect.centery) > separation_radius: continue
            
            other_vec = pygame.math.Vector2(enemy.hitbox.center)
            dist = my_vec.distance_to(other_vec)
            
            if dist < separation_radius:
                diff = my_vec - other_vec
                if diff.magnitude() == 0:
                    diff = pygame.math.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                
                # Soft-force: strength decreases linearly with distance
                strength = (separation_radius - dist) / separation_radius
                separation += diff.normalize() * strength
                count += 1
                
        if count > 0:
            separation = separation / count
            if separation.magnitude() > 0:
                 separation = separation.normalize()
                 
        return separation

    def attack_player(self, target=None):
        if target is None: target = self.player

        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time > self.attack_cooldown:
            # Picu animasi
            self.status = 'attack'
            self.frame_index = 0
            self.last_attack_time = current_time
            
            # Terapkan damage ke pemain
            if hasattr(target, 'take_damage'):
                target.take_damage(self.damage, self.pos)

    def check_player_attacks(self):
        # Gaya Survivors: Cek daftar hitbox atau satu hitbox
        hitboxes = getattr(self.player, 'attack_hitboxes', [])
        if not hitboxes and hasattr(self.player, 'attack_hitbox') and self.player.attack_hitbox:
            hitboxes = [self.player.attack_hitbox]
            
        hit = False
        my_points = self.get_world_hitbox_points()
        for hb in hitboxes:
            if SAT.collides(my_points, hb):
                hit = True
                break
        
        if hit and not self.is_hurting:
            # Deal damage
            damage_dealt = self.player.damage
            self.health -= damage_dealt
            
            # Lifesteal logic
            if hasattr(self.player, 'lifesteal') and self.player.lifesteal > 0:
                hp_gain = damage_dealt * self.player.lifesteal
                self.player.health = min(self.player.max_health, self.player.health + hp_gain)

            # Visual Groups saja
            visual_groups = [g for g in self.groups() if hasattr(g, 'custom_draw')]
            if not visual_groups and self.groups(): visual_groups = [self.groups()[0]]
            HitSpark(self.hitbox.center, visual_groups)
            
            kb_direction = pygame.math.Vector2(self.rect.center) - pygame.math.Vector2(self.player.rect.center)
            if kb_direction.magnitude() > 0:
                kb_strength = self.player.weapon_data.get('knockback', 10)
                self.knockback_vector = kb_direction.normalize() * kb_strength
            
            # Efek Hit Stop
            if self.game:
                if not self.game.is_hit_stopped:
                    self.game.is_hit_stopped = True
                    self.game.hit_stop_timer = pygame.time.get_ticks()

                if self.health <= 0:
                    self.is_dead = True
                else:
                    self.is_hurting = True
                    self.hurt_time = pygame.time.get_ticks()
                self.frame_index = 0

    def collision(self, direction, vel, obstacle_sprites, enemy_sprites=None):
        # OPTIMASI: Filter rintangan terdekat
        # Kami pakai sensor lokal karena iterasi 4000+ pohon terlalu lambat
        sensor_rect = self.hitbox.inflate(10, 10)
        sensor_sprite = pygame.sprite.Sprite()
        sensor_sprite.rect = sensor_rect
        
        nearby_obstacles = pygame.sprite.spritecollide(sensor_sprite, obstacle_sprites, False)
        
        # Rintangan
        for sprite in nearby_obstacles:
            target_hit = getattr(sprite, 'hitbox', sprite.rect)
            if target_hit.colliderect(self.hitbox):
                if direction == 'horizontal':
                    if vel > 0: self.hitbox.right = target_hit.left
                    else: self.hitbox.left = target_hit.right
                    self.pos.x = self.hitbox.centerx - self.rect.width/2
                if direction == 'vertical':
                    if vel > 0: self.hitbox.bottom = target_hit.top
                    else: self.hitbox.top = target_hit.bottom
                    self._sync_pos_with_hitbox()
