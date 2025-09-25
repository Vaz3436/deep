import pygame
import sys
import random
from player import (
    Player, Projectile,
    Enemy, ShooterEnemy, JumperEnemy, EnemyProjectile
)

# --- Settings ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# --- Colors ---
Grey = (146, 142, 133)
Dark_Grey = (59, 59, 59)
HEALTH_BAR_COLOR = (255, 0, 0)
HEALTH_BAR_BG_COLOR = (100, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossbow Game")
clock = pygame.time.Clock()

# --- Wall class ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(Dark_Grey)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Particle (optional visual) ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color=(255, 200, 100)):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = random.randint(10, 20)

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.life -= 1
        if self.life <= 0:
            self.kill()

# --- Create game objects/groups ---
player = Player(WIDTH // 2, HEIGHT // 2)
player_group = pygame.sprite.GroupSingle(player)
projectile_group = pygame.sprite.Group()
enemy_projectile_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group()

# Walls: 100px borders
walls = pygame.sprite.Group()
walls.add(Wall(0, 0, WIDTH, 100))               # Top
walls.add(Wall(0, HEIGHT - 100, WIDTH, 100))    # Bottom
walls.add(Wall(0, 0, 100, HEIGHT))              # Left
walls.add(Wall(WIDTH - 100, 0, 100, HEIGHT))    # Right

# playable rectangle inside the walls
playable_rect = pygame.Rect(100, 100, WIDTH - 200, HEIGHT - 200)

# spawn helper (inside playable area and far from player)
def spawn_enemy_of_type(enemy_cls, min_distance=150):
    attempts = 0
    while True:
        x = random.randint(playable_rect.left + 20, playable_rect.right - 20)
        y = random.randint(playable_rect.top + 20, playable_rect.bottom - 20)
        dist = math_dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        attempts += 1
        if dist > min_distance or attempts > 100:
            return enemy_cls(x, y)

# wave system: only shooters and jumpers
wave = 1

def spawn_wave(wave_num):
    # scale counts with wave number
    # more shooters and jumpers as wave grows
    num_shooters = random.randint(1, 1 + wave_num)
    num_jumpers = random.randint(0, max(1, wave_num // 1))  # at least sometimes
    spawned = []
    for _ in range(num_shooters):
        e = spawn_enemy_of_type(ShooterEnemy)
        enemy_group.add(e)
        spawned.append(e)
    for _ in range(num_jumpers):
        e = spawn_enemy_of_type(JumperEnemy)
        enemy_group.add(e)
        spawned.append(e)
    return spawned

# initial wave
spawn_wave(wave)

# HUD
score = 0
font = pygame.font.SysFont(None, 32)
paused = False
pause_font = pygame.font.SysFont(None, 72)

# --- Main loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                paused = not paused

    if not paused:
        keys = pygame.key.get_pressed()

        # shooting (arrow keys)
        if player.can_attack():
            if keys[pygame.K_UP]:
                proj = player.attack("up")
                projectile_group.add(proj)
            elif keys[pygame.K_DOWN]:
                proj = player.attack("down")
                projectile_group.add(proj)
            elif keys[pygame.K_LEFT]:
                proj = player.attack("left")
                projectile_group.add(proj)
            elif keys[pygame.K_RIGHT]:
                proj = player.attack("right")
                projectile_group.add(proj)

        # Updates
        player_group.update(walls, keys)
        projectile_group.update(walls, playable_rect)
        enemy_projectile_group.update(walls, playable_rect)
        particle_group.update()

        # update enemies (pass enemy_projectile_group so shooters can add)
        for e in list(enemy_group):
            e.update(player, walls, playable_rect, enemy_projectile_group)

        # Projectile hits enemies
        collisions = pygame.sprite.groupcollide(projectile_group, enemy_group, True, False)
        for proj, hit_list in collisions.items():
            for en in hit_list:
                dead = en.take_hit()
                # spawn particles
                for _ in range(6):
                    particle_group.add(Particle(proj.rect.centerx, proj.rect.centery, color=(255, 180, 80)))
                if dead:
                    en.kill()
                    score += 1

        # Enemy projectile hits player
        for eproj in list(enemy_projectile_group):
            if player.rect.colliderect(eproj.rect):
                eproj.kill()
                if player.health > 0:
                    player.health -= 1

        # Enemy touches player (melee damage)
        for en in enemy_group:
            if player.rect.colliderect(en.rect):
                if player.health > 0:
                    player.health -= 1
                # small pushback
                dx = player.rect.centerx - en.rect.centerx
                dy = player.rect.centery - en.rect.centery
                dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
                push_back = 16
                player.pos[0] += (push_back * dx / dist)
                player.pos[1] += (push_back * dy / dist)
                player.rect.center = (int(player.pos[0]), int(player.pos[1]))

        # If wave cleared -> next wave
        if len(enemy_group) == 0:
            wave += 1
            spawn_wave(wave)

    # --- Drawing ---
    screen.fill(Grey)
    walls.draw(screen)
    player_group.draw(screen)
    projectile_group.draw(screen)
    enemy_group.draw(screen)
    enemy_projectile_group.draw(screen)
    particle_group.draw(screen)

    # health bar
    bar_x, bar_y = 10, 10
    bar_w, bar_h = 150, 20
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (bar_x, bar_y, bar_w, bar_h))
    hw = int(bar_w * (player.health / player.PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (bar_x, bar_y, max(0, hw), bar_h))

    # score + wave
    score_surf = font.render(f"Score: {score}", True, BLACK)
    wave_surf = font.render(f"Wave: {wave}", True, BLACK)
    screen.blit(score_surf, (10, 40))
    screen.blit(wave_surf, (10, 70))

    # pause overlay
    if paused:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((20, 20, 20))
        screen.blit(overlay, (0, 0))
        p = pause_font.render("PAUSED", True, WHITE)
        screen.blit(p, p.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    pygame.display.flip()
    clock.tick(FPS)
