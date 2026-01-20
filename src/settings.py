
import pygame

# Umum
TITLE = "Survivor Jancok"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 64
CAMERA_ZOOM = 2.4
FPS = 0 # 0 artinya uncapped
DEBUG_MODE = False

# Warna (Premium Palette)
# Background gelap, aksen Neon
COLORS = {
    "BACKGROUND": (10, 10, 18),       # Biru/hitam sangat gelap
    "TEXT": (240, 240, 255),          # Putih tulang agar mudah dibaca
    "TEXT_HOVER": (100, 255, 218),    # Neon Cyan/Teal
    "ACCENT": (120, 80, 255),         # Neon Ungu
    "BUTTON_BG": (30, 30, 45),        # Abu gelap/biru
    "BUTTON_BORDER": (60, 60, 80)     # Abu lebih terang
}

# Font
FONT_NAME = "arial" # Fallback, akan coba load yang lebih bagus jika ada
FONT_SIZE_TITLE = 80
FONT_SIZE_MENU = 40

# Pemain
PLAYER_SPEED = 5
ANIMATION_SPEED = 0.15 # Frame per update
ATTACK_ANIMATION_SPEED = 0.5 # Serangan lebih cepat
DASH_SPEED = 15
DASH_DURATION = 150 # ms
DASH_COOLDOWN = 600 # ms

# Kamera & Peta
CAMERA_ZOOM = 1.5 
TILE_SIZE = 64
CHUNK_SIZE = 16 # Tile per chunk
LOAD_RADIUS = 3 # Radius chunk yang dimuat di sekitar pemain

# AI Orc
ORC_SPEED = 2.5
ORC_CHASE_RANGE = 2500
ORC_ATTACK_RANGE = 45
ORC_ANIMATION_SPEED = 0.15

# Pertarungan
PLAYER_HEALTH = 100
PLAYER_ATTACK_COOLDOWN = 300 # ms
PLAYER_DAMAGE = 20

# Data Karakter
CHARACTER_DATA = {
    'adventurer': {
        'name': 'Knight',
        'health': 100,
        'speed': 5,
        'damage': 20,
        'asset_path': "assets/Characters/Adventurer",
        'description': "Petarung seimbang dengan versatilitas tinggi.",
        'starting_weapon': 'sword'
    },
    'female': {
        'name': 'Female Mage',
        'health': 80,
        'speed': 6,
        'damage': 15,
        'asset_path': "assets/Characters/Female",
        'description': "Prajurit lincah dengan kecepatan tinggi.",
        'starting_weapon': 'fireball',
        'frame_size': (48, 64)
    }
}

# Data Musuh
ENEMY_DATA = {
    'orc': {
        'name': 'Orc',
        'health': 3,
        'speed': 2.5,
        'damage': 10,
        'asset_path': "assets/Characters/Orc/Orc with shadows",
        'exp_drop': 30,
        'chase_range': 2500,
        'attack_range': 80,
        'scale': 2.0
    },
    'orc_captain': {
        'name': 'Orc Captain',
        'health': 60,  # 20x the health of a regular orc (3 * 20)
        'speed': 1.8, # Slower but heavier
        'damage': 25, # More punch
        'asset_path': "assets/Characters/Orc/Orc with shadows",
        'exp_drop': 500, # Big reward
        'chase_range': 3000,
        'attack_range': 120,
        'scale': 4.5 # Massive size
    }
}

# Data Senjata
WEAPON_DATA = {
    'sword': {
        'name': 'Bronze Sword',
        'damage': 20,
        'cooldown': 900,
        'range': 110,
        'width': 200,
        'slash_color': (255, 255, 255),
        'projectile_count': 1,
        'knockback': 12
    },
    'aura': {
        'name': 'Holy Aura',
        'damage': 10,
        'cooldown': 200, # Tick rate (Cepat agar terasa responsif)
        'range': 80,
        'color': (255, 215, 0, 100), # Emas
        'knockback': 2
    },
    'fireball': {
        'name': 'Fireball',
        'damage': 35,
        'cooldown': 1200,
        'range': 350, # Jarak deteksi
        'speed': 7,
        'projectile_count': 1,
        'knockback': 20
    }
}

# Resolusi
RESOLUTIONS = [
    (1280, 720),
    (1600, 900),
    (1920, 1080)
]

# Setting Peta Prosedural
MAP_SIZE = 0 # Dinamis

# Skala Kesulitan
INITIAL_SPAWN_COOLDOWN = 2000 # ms
MIN_SPAWN_COOLDOWN = 500 # ms
DIFFICULTY_RAMP_RATE = 0.05 # 5% kenaikan kesulitan per level
DIFFICULTY_INTERVAL = 30000 # Naikkan kesulitan tiap 30 detik

# Mapping Input
INPUT_MAP = {
    'UP': pygame.K_w,
    'DOWN': pygame.K_s,
    'LEFT': pygame.K_a,
    'RIGHT': pygame.K_d,
    'DASH': pygame.K_SPACE,
    'ATTACK': 'MOUSE_1' # String khusus untuk mouse
}


