import pygame

RED = (200, 0, 0)

class Obstacle:
    def __init__(self, x, width=40, gap=120):
        self.x = x
        self.width = width
        self.gap = gap
        self.top = pygame.Rect(x, 0, width, 100)  # à adapter
        self.bottom = pygame.Rect(x, 220, width, 400)

    def update(self, speed=3):
        self.x -= speed
        self.top.x = self.x
        self.bottom.x = self.x

    def draw(self, win):
        pygame.draw.rect(win, RED, self.top)
        pygame.draw.rect(win, RED, self.bottom)
