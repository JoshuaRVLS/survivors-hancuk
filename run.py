import sys
import os

# Ensure the workspace root is in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import GameManager

if __name__ == "__main__":
    game = GameManager()
    game.run()
