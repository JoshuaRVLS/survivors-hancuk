import pygame
import math

class Minimap:
    def __init__(self, manager, player):
        self.manager = manager
        self.player = player
        self.radius = 70
        self.margin = 20
        self.scale = 0.08 # Zoom level
        
    def draw(self, surf):
        # Settings
        sw, sh = self.manager.resolution
        center = (sw - self.radius - self.margin, self.radius + self.margin)
        
        # 1. Background
        # Create a temp surface for alpha blending
        m_surf = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(m_surf, (10, 20, 30, 200), (self.radius, self.radius), self.radius)
        
        # 2. Grid lines (Concentric)
        pygame.draw.circle(m_surf, (50, 200, 200, 50), (self.radius, self.radius), self.radius * 0.6, 1)
        pygame.draw.circle(m_surf, (50, 200, 200, 100), (self.radius, self.radius), self.radius, 2)
        
        # 3. Enemies
        # Access enemy_sprites via the active scene (GameScene)
        # We assume manager.game.active_scene is GameScene or similar
        scene = self.manager.active_scene
        if hasattr(scene, 'enemy_sprites'):
            for enemy in scene.enemy_sprites:
                # SAFEGUARD: Ignore VFX or non-entities that ended up here
                if not hasattr(enemy, 'pos') or not hasattr(self.player, 'pos'):
                    continue
                    
                # Relative pos
                rel = (enemy.pos - self.player.pos) * self.scale
                dist = rel.magnitude()
                
                if dist < self.radius - 4:
                     # Draw red dot
                     enemy_pos = (self.radius + rel.x, self.radius + rel.y)
                     pygame.draw.circle(m_surf, (255, 50, 50), enemy_pos, 3)

        # 4. Chests (Interactables)
        if hasattr(scene, 'interactable_sprites'):
            for item in scene.interactable_sprites:
                if not hasattr(item, 'pos'): continue
                
                # Check for "state" to filter opened chests (Optional)
                if hasattr(item, 'state') and item.state == 'open':
                    continue
                    
                rel = (item.pos - self.player.pos) * self.scale
                dist = rel.magnitude()
                
                if dist < self.radius - 4:
                    # Draw Yellow Dot
                    item_pos = (self.radius + rel.x, self.radius + rel.y)
                    pygame.draw.circle(m_surf, (255, 215, 0), item_pos, 3)

        # 4. Player (Center)
        pygame.draw.circle(m_surf, (255, 255, 255), (self.radius, self.radius), 4)
        
        # 5. Scanner Line
        angle = (pygame.time.get_ticks() / 1500.0) * (2 * math.pi)
        scan_end = (self.radius + math.cos(angle) * self.radius, self.radius + math.sin(angle) * self.radius)
        pygame.draw.line(m_surf, (0, 255, 100, 150), (self.radius, self.radius), scan_end, 2)
        
        # 6. Blit to UI
        surf.blit(m_surf, (center[0] - self.radius, center[1] - self.radius))
