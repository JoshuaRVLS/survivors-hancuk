import pygame

# Caching loaded sheets to prevent disk I/O lag on every spawn
_SPRITE_CACHE = {}

def load_sprite_sheet(path, frame_width, frame_height, scale=1, trim=False):
    """
    Load a sprite sheet and return a list of individual frame surfaces.
    If trim is True, it crops empty space around the non-transparent pixels.
    """
    # Check Cache
    cache_key = (path, frame_width, frame_height, scale, trim)
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]

    try:
        sheet = pygame.image.load(path).convert_alpha()
    except FileNotFoundError:
        print(f"Error: Could not load sprite sheet at {path}")
        return []

    sheet_width, sheet_height = sheet.get_size()
    frames = []

    for y in range(0, sheet_height, frame_height):
        for x in range(0, sheet_width, frame_width):
            frame = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), (x, y, frame_width, frame_height))
            
            if trim:
                # Find the bounding box of the non-transparent pixels
                rect = frame.get_bounding_rect()
                if rect.width > 0 and rect.height > 0:
                    frame = frame.subsurface(rect).copy()

            if scale != 1:
                frame = pygame.transform.scale(frame, (int(frame.get_width() * scale), int(frame.get_height() * scale)))
            
            frames.append(frame)
    
    # Store in Cache
    _SPRITE_CACHE[cache_key] = frames
    
    return frames

def debug_log(*args, **kwargs):
    """Prints to console only if game.debug_mode is global and enabled."""
    import __main__
    game = getattr(__main__, 'game', None)
    if game and getattr(game, 'debug_mode', False):
        print("[DEBUG]", *args, **kwargs)

def get_cache_info():
    """Returns stats about the sprite cache."""
    return {
        "entries": len(_SPRITE_CACHE),
        "keys": list(_SPRITE_CACHE.keys())
    }
