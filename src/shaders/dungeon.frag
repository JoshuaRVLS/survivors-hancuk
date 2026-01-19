#version 330 core
uniform sampler2D tex;
uniform sampler2D tex_ui;
uniform float time;
uniform vec2 player_pos;
uniform int render_mode; // 0: Game, 1: Menu
uniform vec3 u_lights[16];
uniform vec3 u_light_colors[16];
uniform int u_light_count;
uniform vec3 u_shadows[16];
uniform int u_shadow_count;

// UI Uniforms
uniform vec4 u_health_rect;
uniform float u_health;
uniform vec4 u_xp_rect;
uniform float u_xp;

in vec2 v_text;
out vec4 f_color;

// Helper: Color Grading (Contrast + Saturation)
vec3 color_grade(vec3 color, float contrast, float saturation) {
    // Contrast
    vec3 c = (color - 0.5) * contrast + 0.5;
    
    // Saturation
    float gray = dot(c, vec3(0.299, 0.587, 0.114));
    vec3 s = mix(vec3(gray), c, saturation);
    
    return clamp(s, 0.0, 1.0);
}

// Helper: UI Bar (Same as before)
vec4 draw_bar(vec2 uv, vec4 rect, float fill, vec3 color, bool pulse) {
    if (uv.x < rect.x || uv.x > rect.x + rect.z || uv.y < rect.y || uv.y > rect.y + rect.w) return vec4(0.0);
    vec2 l_uv = (uv.xy - rect.xy) / rect.zw;
    vec3 out_col = color * 0.15;
    float alpha = 0.6;
    
    if (l_uv.x < fill) {
        alpha = 0.9;
        out_col = mix(color * 0.6, color * 1.4, l_uv.y);
        float shine = smoothstep(0.0, 0.4, 1.0 - abs(l_uv.y - 0.5) * 1.5 - l_uv.x * 0.2);
        out_col += vec3(0.3) * shine;
        if (pulse && fill < 0.3) {
            float p = (sin(time * 15.0) + 1.0) * 0.5;
            out_col += vec3(0.4) * p * (1.0 - l_uv.x);
        }
    }
    if (int(l_uv.x * 50.0) % 2 == 0) out_col *= 0.95;
    return vec4(out_col, alpha);
}

void main() {
    vec2 uv = v_text;
    float aspect = 1.777;
    vec2 uv_aspect = vec2(uv.x * aspect, uv.y);
    
    // --- CHROMATIC ABERRATION (Edge Distortion) ---
    // Strength increases at edges
    float dist_center = distance(uv, vec2(0.5));
    float aber_strength = smoothstep(0.3, 1.0, dist_center) * 0.003; 
    
    // Sample texture with offset channels
    float r = texture(tex, uv - vec2(aber_strength, 0.0)).r;
    float g = texture(tex, uv).g;
    float b = texture(tex, uv + vec2(aber_strength, 0.0)).b;
    
    vec3 raw_world = vec3(r, g, b);
    
    // --- AMBIENT DARKNESS & PLAYER TORCH ---
    vec3 final_world;
    if (render_mode == 0) {
        // Player Torch Radius - MUCH LARGER
        vec2 p_pos_aspect = vec2(player_pos.x * aspect, player_pos.y);
        float p_dist = distance(uv_aspect, p_pos_aspect);
        
        // Torch Flicker
        float flicker = (sin(time * 5.0) * 0.04) + (sin(time * 12.0) * 0.01);
        float torch_rad_inner = 0.45 + flicker;
        float torch_rad_outer = 1.1 + flicker;
        
        // Substantially larger lit area
        float torch = 1.0 - smoothstep(torch_rad_inner, torch_rad_outer, p_dist); 
        
        // Brighter Ambient (Can actually see the world now)
        vec3 ambient_col = vec3(0.35, 0.35, 0.45); 
        
        // Mix world with ambient based on torch light
        final_world = mix(raw_world * ambient_col, raw_world, torch);
        
        // Add a soft warm light glow
        final_world += vec3(0.04, 0.03, 0.01) * torch;
    } else {
        final_world = raw_world;
    }
    
    // --- SHADOWS ---
    if (render_mode == 0) {
        float shadow_factor = 0.0;
        for (int i = 0; i < u_shadow_count; i++) {
            vec2 s_pos = vec2(u_shadows[i].x * aspect, u_shadows[i].y);
            float s_dist = distance(uv_aspect, s_pos);
            float s_rad = u_shadows[i].z;
            float s = 1.0 - smoothstep(0.0, s_rad, s_dist);
            shadow_factor += s * 0.4; // Softer shadows
        }
        shadow_factor = min(shadow_factor, 0.7);
        final_world *= (1.0 - shadow_factor);
    }
    
    // --- ADDITIVE LIGHTS (Glow) ---
    if (render_mode == 0) {
        vec3 glow = vec3(0.0);
        for (int i = 0; i < u_light_count; i++) {
            vec2 l_pos = vec2(u_lights[i].x * aspect, u_lights[i].y);
            float l_dist = distance(uv_aspect, l_pos);
            float l_rad = u_lights[i].z;
            
            float g = 1.0 - smoothstep(0.0, l_rad * 1.5, l_dist);
            glow += u_light_colors[i] * pow(g, 1.3) * 0.4; 
        }
        final_world += glow;
    }
    
    // --- VIBRANT COLOR GRADING ---
    final_world = color_grade(final_world, 1.15, 1.25);
    
    // --- VIGNETTE (Subtle & Wide) ---
    float vig = 1.0 - smoothstep(0.6, 1.5, dist_center);
    final_world *= mix(0.85, 1.0, vig); // Very soft corners (0.85)
    
    // --- RENDER MODE SPECIFICS ---
    if (render_mode == 2) { 
        // Menu/Pause: Grayscale + Darker
         float gray = dot(final_world, vec3(0.299, 0.587, 0.114));
         final_world = vec3(gray) * 0.5;
    }
    
    // --- UI BARS ---
    if (render_mode == 0) {
        vec4 hp_bar = draw_bar(uv, u_health_rect, u_health, vec3(1.0, 0.1, 0.3), true);
        final_world = mix(final_world, hp_bar.rgb, hp_bar.a);
        
        vec4 xp_bar = draw_bar(uv, u_xp_rect, u_xp, vec3(0.0, 0.8, 1.0), false);
        final_world = mix(final_world, xp_bar.rgb, xp_bar.a);
    }
    
    // --- UI LAYER ---
    vec4 ui_color = texture(tex_ui, uv);
    vec3 final_color = mix(final_world, ui_color.rgb, ui_color.a);
    
    f_color = vec4(final_color, 1.0);
}
