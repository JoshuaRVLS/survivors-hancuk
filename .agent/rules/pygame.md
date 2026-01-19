---
trigger: always_on
glob:
description:
---

## 1. Tech Stack & Compatibility
- **Core:** Use Python 3.12+, Pygame-CE, and ModernGL.
- **Rendering:** Strict separation between Pygame (Logic/CPU) and ModernGL (Visuals/GPU).
- **Initialization:** Always use `pygame.display.set_mode((w, h), pygame.OPENGL | pygame.DOUBLEBUF)`.

## 2. Rendering Pipeline (The Hybrid Rule)
- **Software Buffer:** Draw all game logic and standard sprites onto a `pygame.Surface` named `internal_surface`.
- **Texture Conversion:** Every frame, convert `internal_surface` into a `moderngl.Texture`.
- **Final Pass:** Render a full-screen quad (Screen-Aligned Triangle Strip) using the texture as input to a Post-Process Fragment Shader.
- **NEVER** use `screen.blit()` directly to the display window once OpenGL is initialized.

## 3. Shader Development (GLSL)
- **GLSL Version:** Use `#version 330 core` for maximum compatibility and performance.
- **Uniforms:** Use `u_time` (float) for animations, `u_resolution` (vec2) for scaling, and `u_texture` (sampler2D) for the game surface.
- **Coord System:** Use normalized coordinates (0.0 to 1.0) inside GLSL for resolution independence.
- **Storage:** Prefer storing shaders in separate `.glsl` files or a dedicated `Shaders` class; do not hardcode long GLSL strings in logic classes.

## 4. Performance & Resource Management
- **Instancing:** For bullets or particles (>100 objects), use ModernGL `Context.instance` instead of individual draw calls.
- **Memory:** Always call `release()` on ModernGL objects (VAOs, VBOs, Textures) when they are no longer needed to prevent GPU memory leaks.
- **Texture Atlases:** Batch small sprites into a single texture atlas. Ask for UV mapping logic rather than multiple texture bindings.

## 5. Coding Standards & AI Interaction
- **Type Hinting:** Use strict type hints for all functions (e.g., `ctx: mgl.Context`, `surf: pg.Surface`).
- **Decoupling:** Game logic (movement, health, physics) must reside in `entities/` and must not contain OpenGL/ModernGL code.
- **Iterative Tweaks:** When modifying shader effects, change the **Uniforms** first before rewriting the GLSL math.

## 6. Project Structure Preference
/src
  /core
    - engine.py    # ModernGL Context & Quad setup
    - renderer.py  # Shader compilation & Post-processing
  /entities
    - player.py    # Sprite logic & state
  /assets
    /shaders       # .frag and .vert files
    /textures      # .png spritesheets
