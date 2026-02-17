import pygame
import sys
import os
import random


def resource_path(relative_path):
    """Donne le chemin correct pour PyInstaller ou IDE."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)


class Player:
    def __init__(self, x, y, screen_height, speed_multiplier=1.0):
        self.x = x
        self.y = y
        self.target_y = y
        self.base_speed = 30
        self.speed = int(self.base_speed * speed_multiplier)
        self.screen_height = screen_height

        # --- Image du cube ---
        full_image = pygame.image.load(resource_path('cube.png')).convert_alpha()
        rect = full_image.get_bounding_rect()
        cropped = full_image.subsurface(rect)

        self.size = 150
        self.image_original = pygame.transform.scale(cropped, (self.size, self.size))

        # Couleur du cube (par défaut noir)
        self.color = (0, 0, 0)
        self.colored_image = self._recolor(self.image_original, self.color)
        self.image = self.colored_image

        # --- RECT (OBLIGATOIRE) ---
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

        # --- HITBOX (plus petite pour éviter les fausses collisions) ---
        self.hitbox = self.rect.inflate(-30, -30)

        # --- Rotation ---
        self.angle = 0
        self.rotating = False
        self.rotation_speed = int(20 * speed_multiplier)
        self.rotation_target = 0

        # --- Mouvement verrouillé ---
        self.moving = False

        # --- Particules ---
        self.particles = []
        self.emitting = False
        self.emit_direction = None
        self.max_particles = 300

        # --- État d'explosion ---
        self.is_exploding = False
        self.explosion_particles = []

    def set_color(self, color):
        """Met à jour la couleur du cube et régénère l'image recolorée."""
        try:
            self.color = tuple(max(0, min(255, int(c))) for c in color)
        except Exception:
            self.color = (0, 0, 0)
        self.colored_image = self._recolor(self.image_original, self.color)
        self.image = self.colored_image

    def update(self):
        keys = pygame.key.get_pressed()

        # --- Input (si pas déjà en mouvement et pas en train d'exploser) ---
        if not self.moving and not self.is_exploding:
            if keys[pygame.K_UP] and not keys[pygame.K_DOWN]:
                self.target_y = 0
                self.start_rotation(-90)
                self.moving = True

            elif keys[pygame.K_DOWN] and not keys[pygame.K_UP]:
                self.target_y = self.screen_height - self.size
                self.start_rotation(90)
                self.moving = True

        # --- Mouvement ---
        if not self.is_exploding:
            if abs(self.y - self.target_y) > self.speed:
                self.y += self.speed if self.y < self.target_y else -self.speed
            else:
                self.y = self.target_y
                self.moving = False

            # --- Rotation fluide ---
            if self.rotating:
                if abs(self.angle - self.rotation_target) > self.rotation_speed:
                    self.angle += self.rotation_speed if self.angle < self.rotation_target else -self.rotation_speed
                else:
                    self.angle = self.rotation_target
                    self.rotating = False

                # utiliser l'image recolorée pour la rotation afin d'afficher la couleur
                self.image = pygame.transform.rotate(self.colored_image, self.angle)
            else:
                self.angle = 0
                self.image = self.colored_image

        # --- Mise à jour RECT ---
        self.rect.topleft = (self.x, self.y)

        # --- Mise à jour HITBOX ---
        self.hitbox.center = self.rect.center

        # --- Particules: update & emission pendant la rotation ---
        if self.rotating and self.emitting:
            if len(self.particles) < self.max_particles:
                for _ in range(3):
                    px = self.rect.centerx + random.uniform(-10, 10)
                    if self.emit_direction == 'up':
                        py = self.rect.bottom + random.uniform(0, 10)
                        vy = random.uniform(1.0, 3.5)
                    else:
                        py = self.rect.top + random.uniform(-10, 0)
                        vy = random.uniform(-3.5, -1.0)
                    vx = random.uniform(-1.5, 1.5)
                    radius = random.uniform(4.0, 10.0)
                    life = random.randint(18, 36)
                    self.particles.append(Particle(px, py, vx, vy, life, radius, self.color))

        # Update particles
        alive = []
        for p in self.particles:
            p.update()
            if p.alive:
                alive.append(p)
        self.particles = alive

        # Update explosion particles
        if self.is_exploding:
            alive_explosion = []
            for p in self.explosion_particles:
                p.update()
                if p.alive:
                    alive_explosion.append(p)
            self.explosion_particles = alive_explosion

    def start_rotation(self, angle):
        self.angle = 0
        self.rotation_target = angle
        self.rotating = True
        # Commence l'émission de particules pour la traînée
        self.emitting = True
        self.emit_direction = 'up' if angle < 0 else 'down'

    def explode(self):
        """Crée une explosion en morceaux dans toutes les directions."""
        self.is_exploding = True
        self.moving = False
        self.emitting = False

        num_fragments = random.randint(20, 30)
        for _ in range(num_fragments):
            angle = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(4, 12)
            vx = speed * __import__('math').cos(angle)
            vy = speed * __import__('math').sin(angle)
            px = self.rect.centerx
            py = self.rect.centery
            radius = random.uniform(8.0, 15.0)
            life = random.randint(30, 50)
            self.explosion_particles.append(Particle(px, py, vx, vy, life, radius, self.color))

    def is_explosion_finished(self):
        return self.is_exploding and len(self.explosion_particles) == 0

    def draw(self, win):
        # Draw particles first so elles restent derrière le cube
        for p in self.particles:
            p.draw(win)

        # Draw explosion particles
        for p in self.explosion_particles:
            p.draw(win)

        # Ne pas dessiner le cube si l'explosion est en cours
        if not self.is_exploding:
            draw_rect = self.image.get_rect(center=(self.rect.centerx, self.rect.centery))
            win.blit(self.image, draw_rect)

    def _recolor(self, surf, color):
        """Retourne une copie de `surf` recolorée en `color` tout en conservant l'alpha."""
        new = surf.copy().convert_alpha()
        w, h = new.get_size()
        for x in range(w):
            for y in range(h):
                r, g, b, a = surf.get_at((x, y))
                if a == 0:
                    continue
                new.set_at((x, y), (color[0], color[1], color[2], a))
        return new


class Particle:
    def __init__(self, x, y, vx, vy, life, radius, color=(0, 0, 0)):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.life = int(life)
        self.max_life = int(life)
        self.radius = float(radius)
        self.alive = True
        try:
            self.color = tuple(max(0, min(255, int(c))) for c in color)
        except Exception:
            self.color = (0, 0, 0)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        # légère décélération
        self.vx *= 0.98
        self.vy *= 0.98
        self.life -= 1
        # rétrécissement
        self.radius *= 0.98
        if self.life <= 0 or self.radius < 0.6:
            self.alive = False

    def draw(self, win):
        alpha = max(0, min(255, int(255 * (self.life / max(1, self.max_life)))))
        r = max(1, int(self.radius))
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (self.color[0], self.color[1], self.color[2], alpha), (r, r), r)
        win.blit(surf, (int(self.x) - r, int(self.y) - r))