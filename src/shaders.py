import moderngl
import pygame
import numpy as np
from array import array

class ShaderPipeline:
    def __init__(self, size):
        self.ctx = moderngl.create_context()
        self.size = size
        
        # Load Shaders
        with open('src/shaders/default.vert', 'r') as f:
            vert = f.read()
        with open('src/shaders/dungeon.frag', 'r') as f:
            frag = f.read()
            
        self.program = self.ctx.program(vertex_shader=vert, fragment_shader=frag)
        
        # Fullscreen Quad
        # x, y, u, v
        self.vbo = self.ctx.buffer(np.array([
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 0.0,
        ], dtype='f4'))
        self.vao = self.ctx.vertex_array(self.program, [(self.vbo, '2f 2f', 'in_vert', 'in_text' if 'in_text' in self.program else 'in_texcoord')])
        
        # Textures
        self.texture = self.ctx.texture(size, 4)
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture.swizzle = 'BGRA' # Changed from RGBA to fix swapped Red/Blue channels
        
        self.texture_ui = self.ctx.texture(size, 4)
        self.texture_ui.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture_ui.swizzle = 'BGRA' # Changed from RGBA to fix swapped Red/Blue channels
        
        # Set texture units
        if 'tex' in self.program:
            self.program['tex'].value = 0
        if 'tex_ui' in self.program:
            self.program['tex_ui'].value = 1

    def render(self, surface, ui_surface=None, player_pos=(0.5, 0.5), render_mode=0, lights=[], shadows=[], bar_data=None):
        # Update World Texture
        self.texture.write(surface.get_view('1'))
        self.texture.use(0)
        
        # Update UI Texture
        if ui_surface:
            self.texture_ui.write(ui_surface.get_view('1'))
        self.texture_ui.use(1)
        
        # Update uniforms
        if 'time' in self.program:
            self.program['time'].value = pygame.time.get_ticks() / 1000.0
        if 'player_pos' in self.program:
            self.program['player_pos'].value = player_pos
        if 'render_mode' in self.program:
            self.program['render_mode'].value = render_mode
            
        # Pass Bar Data (Health/XP)
        if 'u_health' in self.program and bar_data:
            bd = bar_data
            self.program['u_health'].value = bd.get('health', 1.0)
            self.program['u_xp'].value = bd.get('xp', 0.0)
            self.program['u_health_rect'].value = bd.get('health_rect', (0,0,0,0))
            self.program['u_xp_rect'].value = bd.get('xp_rect', (0,0,0,0))
            
        # Pass dynamic light data
        if 'u_light_count' in self.program:
            count = min(len(lights), 16)
            self.program['u_light_count'].value = count
            
            # Pad to 16 lights - ONLY pass x, y, radius (first 3 elements)
            light_data = [l[:3] for l in lights[:16]]
            padded_lights = light_data + [(0.0, 0.0, 0.0)] * (16 - len(light_data))
            self.program['u_lights'].value = padded_lights
            
            # Pad colors
            light_colors = [l[3] if len(l) > 3 else (1.0, 1.0, 1.0) for l in lights[:16]]
            padded_colors = light_colors + [(0.0, 0.0, 0.0)] * (16 - len(light_colors))
            if 'u_light_colors' in self.program:
                self.program['u_light_colors'].value = padded_colors

        # Pass dynamic shadow data
        if 'u_shadow_count' in self.program:
            count = min(len(shadows), 16)
            self.program['u_shadow_count'].value = count
            padded_shadows = shadows[:16] + [(0.0, 0.0, 0.0)] * (16 - len(shadows))
            self.program['u_shadows'].value = padded_shadows
            
        # Clear and Draw
        self.ctx.viewport = (0, 0, self.size[0], self.size[1])
        self.ctx.clear(0.0, 0.0, 0.0)
        self.vao.render(moderngl.TRIANGLE_STRIP)

    def resize(self, size):
        self.size = size
        # Re-release and re-create textures
        self.texture.release()
        self.texture = self.ctx.texture(size, 4)
        self.texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture.swizzle = 'BGRA' # Fixed: must match __init__ to prevent color swap
        
        self.texture_ui.release()
        self.texture_ui = self.ctx.texture(size, 4)
        self.texture_ui.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.texture_ui.swizzle = 'BGRA' # Fixed: must match __init__ to prevent color swap
