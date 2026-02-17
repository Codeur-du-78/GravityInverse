# ================ IMPORTS-Modules =================
import os
import pygame
import sys
import random
import colorsys
from cube import Player
import json
os.environ.setdefault("SDL_AUDIODRIVER", "directsound")
# ================= CHEMIN POUR PYINSTALLER =================
def resource_path(relative_path):
    """Donne le chemin correct pour PyInstaller ou IDE."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()
mixer_failed = False
try:
    pygame.mixer.init()
    print("Fichiers audios chargés avec succés !")
except pygame.error as e:
    print("⚠️ 404 ERROR Les fichiers audios sont mals chargés, le jeu fonctionnera sans le son.:", e)
    mixer_failed = True

# ================= FENÊTRE =================
WINDOWED = False
WIN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = WIN.get_size()
pygame.display.set_caption("Gravity Flip")

# ================= COULEURS =================
BLACK = (0, 0, 0)

# ================= POLICES =================
title_font = pygame.font.SysFont("Polya", 80)
score_font = pygame.font.SysFont("Arial Black", 90)
end_font = pygame.font.SysFont("Arial Black", 60)

# Couleur du cube (par défaut noir)
cube_color = (0, 0, 0)

# ================= UI =================
button_size = 100
button_rect = pygame.Rect(WIDTH - button_size - 40, 40, button_size, button_size)
fullscreen_img = pygame.transform.scale(pygame.image.load(resource_path("Boutton.png")), (button_size, button_size))
windowed_img = pygame.transform.scale(pygame.image.load(resource_path("Boutton.png")), (button_size, button_size))

play_img_base = pygame.transform.scale(pygame.image.load(resource_path("button.png")), (850, 350))
play_img_hover = pygame.transform.scale(play_img_base, (900, 390))
play_img = play_img_base
play_rect = play_img.get_rect(center=(WIDTH // 2, HEIGHT // 2))

background_original = pygame.image.load(resource_path("Bühnenbild1.png"))
background = pygame.transform.scale(background_original, (WIDTH, HEIGHT))

# ================= SONS =================
if not mixer_failed:
    try:
        print("Mixeur audio initialisé avec succés !")
        jump_sound = pygame.mixer.Sound(resource_path("530448__mellau__whoosh-short-5.wav"))
        jump_sound.set_volume(0.6)
        
        hit_sound = pygame.mixer.Sound(resource_path("614105__kierham__weird-short-impact.wav"))
        hit_sound.set_volume(0.7)
        
        score_sound = pygame.mixer.Sound(resource_path("523547__lilmati__retro-underwater-coin.wav"))
        score_sound.set_volume(0.4)
        
        SOUNDS_LOADED = True
    except Exception:
        print("⚠️ 404 ERROR Fichiers audio manquants - le jeu fonctionnera sans son")
        SOUNDS_LOADED = False
else:
    print("⚠️ 404 ERROR Mixeur audio non initialisé — le jeu fonctionnera sans son")
    SOUNDS_LOADED = False

# ================= PARAMÈTRES SPIKES =================
INITIAL_SPIKE_SPEED = 8  # Vitesse normale pour mode fenêtré
MAX_SPIKE_SPEED = 100
SPEED_INCREASE_RATE = 0.018
SPAWN_INTERVAL = 90
MIN_SPAWN_INTERVAL = 48

# ================= HIGHSCORE =================
# Fichier de stockage du highscore dans le home de l'utilisateur
HIGHSCORE_FILE = os.path.join(os.path.expanduser("~"), ".gravity_flip_highscore.json")

def load_highscore():
    try:
        if os.path.exists(HIGHSCORE_FILE):
            print("Jeu lancé avec succés !")
            with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return int(data.get("highscore", 0))
    except Exception:
        print("⚠️ 404 ERROR Impossible de lire le highscore")
    return 0

def save_highscore(value):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump({"highscore": int(value)}, f)
            print("Jeu lancé avec succés !")
    except Exception:
        print("⚠️ 404 ERROR Impossible d'enregistrer le highscore")

highscore = load_highscore()

# ================= SPIKE =================
class Spike(pygame.sprite.Sprite):
    def __init__(self, x, speed, height, side, speed_multiplier=1.0):
        super().__init__()
        filename = random.choice([
            "spike A.png",
            "spike B.png",
            "spike C.png",
            "spike D.png"
        ])
        img = pygame.image.load(resource_path(filename)).convert_alpha()
        self.image_original = pygame.transform.scale(img, (150, 150))
        self.image = self.image_original
        self.rect = self.image.get_rect()
        if side == "top":
            self.image = pygame.transform.flip(self.image_original, False, True)
            self.rect.topleft = (x, 0)
        else:
            self.rect.bottomleft = (x, height)
        self.speed = speed * speed_multiplier  # Applique le multiplicateur

    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.kill()

# ================= SPIKE MANAGER =================
class SpikeManager:
    def __init__(self, height, speed_multiplier=1.0):
        self.group = pygame.sprite.Group()
        self.timer = 0
        self.speed = INITIAL_SPIKE_SPEED
        self.spawn_interval = SPAWN_INTERVAL
        self.height = height
        self.pattern_queue = []
        self.min_gap = 260
        self.last_x = WIDTH + 200
        self.speed_multiplier = speed_multiplier  # Stocke le multiplicateur

    def update(self):
        self.timer += 1
        if self.timer >= self.spawn_interval:
            self.timer = 0
            self.spawn_spike()
        self.speed = min(MAX_SPIKE_SPEED, self.speed + SPEED_INCREASE_RATE)
        self.spawn_interval = max(MIN_SPAWN_INTERVAL, self.spawn_interval - 0.04)
        self.min_gap = max(175, self.min_gap - 0.05)
        self.group.update()

    def spawn_spike(self):
        if not self.pattern_queue:
            # Probabilités pondérées pour plus de variété
            patterns_pool = [
                "single", "single",  # 2x plus probable
                "double", "double",  # 2x plus probable
                "zigzag",
                "triple",
                "sandwich",
                "wave",
                "quick_double",
                "chaos",  # NOUVEAU : pattern complètement aléatoire
                "speed_trap"  # NOUVEAU : 2 rapprochés puis gap
            ]
            
            pattern = random.choice(patterns_pool)
            
            if pattern == "single":
                self.pattern_queue = [random.choice(["top", "bottom"])]
            
            elif pattern == "double":
                side = random.choice(["top", "bottom"])
                self.pattern_queue = [side, side]
            
            elif pattern == "zigzag":
                a = random.choice(["top", "bottom"])
                b = "bottom" if a == "top" else "top"
                self.pattern_queue = [a, b, a]
            
            elif pattern == "triple":
                side = random.choice(["top", "bottom"])
                self.pattern_queue = [side, side, side]
            
            elif pattern == "sandwich":
                outer = random.choice(["top", "bottom"])
                inner = "bottom" if outer == "top" else "top"
                self.pattern_queue = [outer, inner, outer]
            
            elif pattern == "wave":
                a = random.choice(["top", "bottom"])
                b = "bottom" if a == "top" else "top"
                self.pattern_queue = [a, b, a, b]
            
            elif pattern == "quick_double":
                a = random.choice(["top", "bottom"])
                b = "bottom" if a == "top" else "top"
                self.pattern_queue = [a, b]
            
            elif pattern == "chaos":
                # 3-5 spikes complètement aléatoires
                num = random.randint(3, 5)
                self.pattern_queue = [random.choice(["top", "bottom"]) for _ in range(num)]
            
            elif pattern == "speed_trap":
                # Piège : 2 du même côté rapprochés
                side = random.choice(["top", "bottom"])
                self.pattern_queue = [side, side]
        
        side = self.pattern_queue.pop(0)
        
        # Variation du gap pour plus de dynamisme
        gap_variation = random.randint(-20, 20)
        actual_gap = max(150, self.min_gap + gap_variation)
        
        spike = Spike(self.last_x + actual_gap, self.speed, self.height, side, self.speed_multiplier)
        self.last_x = spike.rect.x
        self.group.add(spike)

    def draw(self, surface):
        self.group.draw(surface)

# ================= FULLSCREEN =================
def toggle_fullscreen():
    global WIN, WIDTH, HEIGHT, WINDOWED, button_rect, play_rect, background
    if WINDOWED:
        WIN = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = WIN.get_size()
        WINDOWED = False
    else:
        WIDTH, HEIGHT = 1280, 720
        WIN = pygame.display.set_mode((WIDTH, HEIGHT))
        WINDOWED = True
    button_rect = pygame.Rect(WIDTH - button_size - 40, 40, button_size, button_size)
    play_rect.center = (WIDTH // 2, HEIGHT // 2)
    background = pygame.transform.scale(background_original, (WIDTH, HEIGHT))

# ================= MENU =================
def menu_loop():
    global play_img, cube_color
    cursor_hand = False
    # UI: slider pour la couleur du cube
    ui_font = pygame.font.SysFont("Arial", 28)
    slider_h = 28
    # Knob ratio [0..1] where 0 = black, >0 = hue region
    knob_ratio = 0.0
    # Initialize knob_ratio from existing cube_color
    try:
        if tuple(cube_color) == (0, 0, 0):
            knob_ratio = 0.0
        else:
            r0, g0, b0 = (c / 255.0 for c in cube_color)
            h0, s0, v0 = colorsys.rgb_to_hsv(r0, g0, b0)
            # temporary slider_w to compute initial position fraction
            tmp_w = min(700, max(600, WIDTH) - 400)
            black_px_tmp = max(30, int(tmp_w * 0.06))
            black_frac_tmp = black_px_tmp / tmp_w
            knob_ratio = black_frac_tmp + h0 * (1.0 - black_frac_tmp)
    except Exception:
        knob_ratio = 0.0

    knob_x = 0
    dragging = False
    slider_changed = False
    # Create a small preview Player to show recolored `cube.png`
    try:
        preview_player = Player(-9999, -9999, HEIGHT)
        preview_player.set_color(cube_color)
    except Exception:
        preview_player = None
    while True:
        mouse = pygame.mouse.get_pos()
        if play_rect.collidepoint(mouse):
            play_img = play_img_hover
            if not cursor_hand:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                cursor_hand = True
        else:
            play_img = play_img_base
            if cursor_hand:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                cursor_hand = False

        WIN.blit(background, (0, 0))
        # Recompute slider dimensions each frame so they s'adaptent au redimensionnement
        slider_w = min(700, WIDTH - 400)
        slider_rect = pygame.Rect(play_rect.centerx - slider_w // 2, play_rect.top - 120, slider_w, slider_h)
        # Black region width
        black_px = max(30, int(slider_w * 0.06))
        black_frac = black_px / slider_w if slider_w > 0 else 0
        # Pré-générer la barre de teintes avec une zone noire à gauche
        hue_surface = pygame.Surface((slider_w, slider_h), pygame.SRCALPHA)
        # Black strip
        if black_px > 0:
            pygame.draw.rect(hue_surface, (0, 0, 0), (0, 0, black_px, slider_h))
        for x in range(black_px, slider_w):
            h = (x - black_px) / max(1, (slider_w - black_px))
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            pygame.draw.line(hue_surface, (int(r * 255), int(g * 255), int(b * 255)), (x, 0), (x, slider_h))

        # Update knob position from ratio (preserve when resizing)
        knob_x = slider_rect.left + int(knob_ratio * slider_w)
        title = title_font.render("Gravity Flip", True, BLACK)
        WIN.blit(title, (WIDTH // 2 - title.get_width() // 2, 150))

        # Afficher le contrôle de couleur au-dessus du bouton play
        label = ui_font.render("Cube color :", True, BLACK)
        WIN.blit(label, (slider_rect.left, slider_rect.top - 34))
        WIN.blit(hue_surface, slider_rect.topleft)
        pygame.draw.rect(WIN, (0, 0, 0), slider_rect, 2)
        # Knob
        knob_y = slider_rect.centery
        knob_radius = 12
        pygame.draw.circle(WIN, (255, 255, 255), (int(knob_x), int(knob_y)), knob_radius)
        pygame.draw.circle(WIN, (0, 0, 0), (int(knob_x), int(knob_y)), knob_radius, 2)

        # Aperçu du cube à droite — utiliser `cube.png` recoloré si possible
        preview_rect = pygame.Rect(play_rect.right + 40, play_rect.centery - 75, 150, 150)
        if preview_player:
            try:
                # Scale the recolored image to fit preview_rect
                img = preview_player.image
                scaled = pygame.transform.smoothscale(img, (preview_rect.width, preview_rect.height))
                draw_rect = scaled.get_rect(center=preview_rect.center)
                WIN.blit(scaled, draw_rect)
            except Exception:
                pygame.draw.rect(WIN, cube_color, preview_rect)
        else:
            pygame.draw.rect(WIN, cube_color, preview_rect)

        WIN.blit(play_img, play_rect)
        if WINDOWED:
            WIN.blit(fullscreen_img, button_rect)
        else:
            WIN.blit(windowed_img, button_rect)
        pygame.display.update()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(e.pos):
                    toggle_fullscreen()
                elif slider_rect.collidepoint(e.pos):
                    dragging = True
                    slider_changed = True
                    nx = max(slider_rect.left, min(e.pos[0], slider_rect.right))
                    knob_x = nx
                    pos_ratio = (knob_x - slider_rect.left) / slider_w if slider_w > 0 else 0
                    if pos_ratio <= black_frac:
                        knob_ratio = 0.0
                        cube_color = (0, 0, 0)
                    else:
                        h = (pos_ratio - black_frac) / (1.0 - black_frac)
                        r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                        cube_color = (int(r * 255), int(g * 255), int(b * 255))
                    if preview_player:
                        preview_player.set_color(cube_color)
                elif play_rect.collidepoint(e.pos):
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
                    return
            if e.type == pygame.MOUSEBUTTONUP:
                dragging = False
            if e.type == pygame.MOUSEMOTION and dragging:
                mx = e.pos[0]
                nx = max(slider_rect.left, min(mx, slider_rect.right))
                knob_x = nx
                pos_ratio = (knob_x - slider_rect.left) / slider_w if slider_w > 0 else 0
                if pos_ratio <= black_frac:
                    knob_ratio = 0.0
                    cube_color = (0, 0, 0)
                else:
                    knob_ratio = pos_ratio
                    h = (pos_ratio - black_frac) / (1.0 - black_frac)
                    r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
                    cube_color = (int(r * 255), int(g * 255), int(b * 255))
                if preview_player:
                    preview_player.set_color(cube_color)

# ================= ÉCRAN FIN =================
def end_screen(score):
    global highscore
    if score > highscore:
        highscore = score
        try:
            save_highscore(highscore)
        except Exception:
            pass
    while True:
        WIN.blit(background, (0, 0))
        score_txt = end_font.render(f"Score : {score}", True, BLACK)
        high_txt = end_font.render(f"Highscore : {highscore}", True, BLACK)
        WIN.blit(score_txt, (WIDTH // 2 - score_txt.get_width() // 2, HEIGHT // 2 - 80))
        WIN.blit(high_txt, (WIDTH // 2 - high_txt.get_width() // 2, HEIGHT // 2))
        pygame.display.update()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return

# ================= GAME LOOP =================
def game_loop():
    # Multiplicateur de vitesse selon le mode
    speed_multiplier = 1.7 if not WINDOWED else 1.0  # 70% plus rapide en plein écran
    
    player = Player(100, 0, HEIGHT, speed_multiplier)
    # Appliquer la couleur sélectionnée au cube
    try:
        player.set_color(cube_color)
    except Exception:
        pass
    spikes = SpikeManager(HEIGHT, speed_multiplier)
    clock = pygame.time.Clock()
    score = 0
    frame_counter = 0
    last_score_milestone = 0
    
    # (Pas de système de dash — comportement classique)
    
    while True:
        clock.tick(60)
        WIN.blit(background, (0, 0))
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(e.pos):
                    toggle_fullscreen()
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_UP, pygame.K_DOWN):
                    if SOUNDS_LOADED:
                        jump_sound.play()
                # (Espace non utilisé — les contrôles restent UP/DOWN)
        
        player.update()
        spikes.update()
        
        # Maintenir le multiplicateur de vitesse normal des spikes
        spikes.speed_multiplier = speed_multiplier
        
        # (Aucun système de dash à gérer)
        
        frame_counter += 1
        if frame_counter >= 10:
            score += 1
            frame_counter = 0
            if SOUNDS_LOADED and score % 10 == 0 and score != last_score_milestone:
                score_sound.play()
                last_score_milestone = score
        
        score_surface = score_font.render(str(score), True, BLACK)
        WIN.blit(score_surface, (WIDTH - score_surface.get_width() - 40, HEIGHT - score_surface.get_height() - 140))
        
        # (UI minimale — uniquement le score)
        
        for spike in spikes.group:
            if player.hitbox.colliderect(spike.rect):
                if SOUNDS_LOADED:
                    hit_sound.play()
                # Déclencher l'explosion au lieu d'aller directement à end_screen
                player.explode()
                
                # Attendre que l'animation d'explosion soit terminée
                explosion_finished = False
                while not explosion_finished:
                    clock.tick(60)
                    WIN.blit(background, (0, 0))
                    
                    player.update()
                    player.draw(WIN)
                    
                    score_surface = score_font.render(str(score), True, BLACK)
                    WIN.blit(score_surface, (WIDTH - score_surface.get_width() - 40, HEIGHT - score_surface.get_height() - 140))
                    
                    # (Pas d'affichage de dash pendant l'explosion)
                    
                    if WINDOWED:
                        WIN.blit(fullscreen_img, button_rect)
                    else:
                        WIN.blit(windowed_img, button_rect)
                    
                    pygame.display.update()
                    explosion_finished = player.is_explosion_finished()
                    
                    # Gestion des événements pendant l'explosion
                    for e in pygame.event.get():
                        if e.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if e.type == pygame.MOUSEBUTTONDOWN:
                            if button_rect.collidepoint(e.pos):
                                toggle_fullscreen()
                
                end_screen(score)
                return
        
        player.draw(WIN)
        spikes.draw(WIN)
        
        if WINDOWED:
            WIN.blit(fullscreen_img, button_rect)
        else:
            WIN.blit(windowed_img, button_rect)
        
        pygame.display.update()

# ================= LANCEMENT =================
while True:
    menu_loop()
    game_loop()