#version 330 core
uniform sampler2D tex;
uniform float time;
in vec2 v_text;
out vec4 f_color;

void main() {
    vec2 uv = v_text;
    
    // Scanline effect
    float scanline = sin(uv.y * 800.0) * 0.04;
    
    // Chromatic Aberration
    float aberration_amount = 0.002;
    
    float r = texture(tex, uv + vec2(aberration_amount, 0.0)).r;
    float g = texture(tex, uv).g;
    float b = texture(tex, uv - vec2(aberration_amount, 0.0)).b;
    
    vec3 color = vec3(r, g, b);
    
    // Vignette
    float vignette = 1.0 - smoothstep(0.5, 1.5, length(uv - 0.5));
    
    color -= scanline;
    color *= vignette;
    
    f_color = vec4(color, 1.0);
}
