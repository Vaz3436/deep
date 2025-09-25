import pygame
import sys
import random
from player import (
    Player, Projectile,
    Enemy, TankEnemy, ShooterEnemy, JumperEnemy, EnemyProjectile
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

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossbow Game")
clock = pygame.time.Clock()

# --- Wall sprite ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(Dark_Grey)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Particle (hit) ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color=(255, 200, 100)):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.life = random.randint(12, 24)

    def update(self):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.life -= 1
        if self.life <= 0:
            self.kill()

# --- Create objects & groups ---
player = Player(WIDTH // 2, HEIGHT // 2)
player_group = pygame.sprite.GroupSingle(player)
projectile_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemy_projectile_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group()

# Walls are 100px borders
walls = pygame.sprite.Group()
walls.add(Wall(0, 0, WIDTH, 100))               # top
walls.add(Wall(0, HEIGHT - 100, WIDTH, 100))    # bottom
walls.add(Wall(0, 0, 100, HEIGHT))              # left
walls.add(Wall(WIDTH - 100, 0, 100, HEIGHT))    # right

# playable area
playable_rect = pygame.Rect(100, 100, WIDTH - 200, HEIGHT - 200)

# spawn helper: inside playable_rect, far from player
def spawn_enemy_far_from_player(min_distance=150):
    enemy_types = [Enemy, TankEnemy, ShooterEnemy, JumperEnemy]
    while True:
        x = random.randint(playable_rect.left + 20, playable_rect.right - 20)
        y = random.randint(playable_rect.top + 20, playable_rect.bottom - 20)
        # ensure not too close to player
        dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        if dist > min_distance:
            cls = random.choice(enemy_types)
            return cls(x, y)

# initial enemies
for _ in range(5):
    enemy_group.add(spawn_enemy_far_from_player())

# HUD
score = 0
font = pygame.font.SysFont(None, 36)
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

        # shooting with arrow keys (player.attack returns Projectile)
        if player.can_attack():
            if keys[pygame.K_UP]:
                projectile_group.add(player.attack("up"))
            elif keys[pygame.K_DOWN]:
                projectile_group.add(player.attack("down"))
            elif keys[pygame.K_LEFT]:
                projectile_group.add(player.attack("left"))
            elif keys[pygame.K_RIGHT]:
                projectile_group.add(player.attack("right"))

        # updates
        player_group.update(walls, keys)
        projectile_group.update(walls)
        enemy_projectile_group.update(walls, playable_rect)
        particle_group.update()

        # update enemies (shooters will add projectiles into enemy_projectile_group)
        for enemy in list(enemy_group):
            # pass the projectile group so ShooterEnemy can add projectiles
            result = enemy.update(player, walls, playable_rect, enemy_projectile_group)
            # some enemy.update implementations return EnemyProjectile; but ShooterEnemy adds directly now,
            # so we don't need to handle returned objects. (kept for compatibility)
            if isinstance(result, EnemyProjectile):
                enemy_projectile_group.add(result)

        # enemy-player collisions (touch damage)
        for enemy in enemy_group:
            if player.rect.colliderect(enemy.rect):
                if player.health > 0:
                    player.health -= 1
                # small pushback
                dx = player.rect.centerx - enemy.rect.centerx
                dy = player.rect.centery - enemy.rect.centery
                dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
                push_back = 20
                # move player rect and pos
                player_group.sprite.pos[0] += (push_back * dx / dist)
                player_group.sprite.pos[1] += (push_back * dy / dist)
                player_group.sprite.rect.center = (int(player_group.sprite.pos[0]), int(player_group.sprite.pos[1]))

        # projectile -> enemy collisions
        for proj in list(projectile_group):
            hit_enemies = pygame.sprite.spritecollide(proj, enemy_group, False)
            if hit_enemies:
                proj.kill()
                for e in hit_enemies:
                    # call take_hit which sets flash; if dead, remove and add score/particles
                    dead = e.take_hit()
                    if dead:
                        e.kill()
                        score += 1
                    # spawn small particles at impact
                    for _ in range(6):
                        particle_group.add(Particle(proj.rect.centerx, proj.rect.centery, color=(255, 180, 80)))

        # enemy projectile -> player collisions
        for eproj in list(enemy_projectile_group):
            if player.rect.colliderect(eproj.rect):
                eproj.kill()
                if player.health > 0:
                    player.health -= 1

        # optional: spawn more enemies over time (simple timer)
        if random.random() < 0.01:  # ~1% chance per frame to add a new enemy (tune as desired)
            enemy_group.add(spawn_enemy_far_from_player())

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
    health_w = int(bar_w * (player.health / player.PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (bar_x, bar_y, max(0, health_w), bar_h))

    # score
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    screen.blit(score_text, (10, 40))

    # pause overlay
    if paused:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((30, 30, 30))
        screen.blit(overlay, (0, 0))
        pause_text = pause_font.render("PAUSED", True, WHITE)
        screen.blit(pause_text, pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

    pygame.display.flip()
    clock.tick(FPS)
