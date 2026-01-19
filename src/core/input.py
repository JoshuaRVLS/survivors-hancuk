
import pygame
from ..settings import INPUT_MAP

class InputManager:
    @staticmethod
    def is_action_pressed(action):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        
        target = INPUT_MAP.get(action)
        if target is None: return False
        
        if isinstance(target, int):
            return keys[target]
        elif target == 'MOUSE_1':
            return mouse[0]
        elif target == 'MOUSE_2':
            return mouse[1]
        elif target == 'MOUSE_3':
            return mouse[2]
            
        return False

    @staticmethod
    def get_movement_vector():
        direction = pygame.math.Vector2()
        if InputManager.is_action_pressed('UP'): direction.y -= 1
        if InputManager.is_action_pressed('DOWN'): direction.y += 1
        if InputManager.is_action_pressed('LEFT'): direction.x -= 1
        if InputManager.is_action_pressed('RIGHT'): direction.x += 1
        
        if direction.magnitude() > 0:
            direction = direction.normalize()
        return direction
