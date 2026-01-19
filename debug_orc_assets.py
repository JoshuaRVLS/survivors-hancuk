import pygame
import os

pygame.init()
pygame.display.set_mode((1, 1))

base_path = "assets/Characters/Orc/Orc"
files = ["Orc-Idle.png", "Orc-Walk.png", "Orc-Attack01.png"]

print("--- Asset Dimensions ---")
for f in files:
    path = os.path.join(base_path, f)
    if os.path.exists(path):
        img = pygame.image.load(path)
        print(f"{f}: {img.get_width()}x{img.get_height()}")
    else:
        print(f"{f}: Not Found")
