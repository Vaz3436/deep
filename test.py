import pygame
import sys
import random
from player import Player, Projectile, Enemy, ShooterEnemy, JumperEnemy, EnemyProjectile

# --- Settings ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# --- Colors ---
Grey = (146, 142, 133)
Dark_Grey = (59, 59, 59)
HEALTH_BAR_COLOR = (255, 0, 0)
HEALTH_BAR_BG_COLOR = (100, 0, 0)
WHITE = (255, 255, 255)

# --- Init ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossbow Game")
clock = pygame.time.Clock()

# --- Wall Class ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(Dark_Grey)
        self.rect = self.image.get_rect(topleft=(x, y))


# --- Particle Class ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color=(255, 200, 100)):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.lifetime = random.randint(10, 20)

    def update(self):
        self.rect.x += int(self.dx)
        self.rect.y += int(self.dy)
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


# --- Create Game Objects ---
player = Player(WIDTH // 2, HEIGHT // 2)
player_group = pygame.sprite.GroupSingle(player)
projectile_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemy_projectiles = pygame.sprite.Group()
particle_group = pygame.sprite.Group()

# Walls
walls = pygame.sprite.Group()
walls.add(Wall(0, 0, WIDTH, 100))               # Top
walls.add(Wall(0, HEIGHT - 100, WIDTH, 100))    # Bottom
walls.add(Wall(0, 0, 100, HEIGHT))              # Left
walls.add(Wall(WIDTH - 100, 0, 100, HEIGHT))    # Right


# --- Enemy Spawning ---
def spawn_enemy_type():
    """Randomly pick an enemy type with weighting."""
    r = random.random()
    if r < 0.6:   # 60% normal
        return Enemy
    elif r < 0.85:  # 25% shooter
        return ShooterEnemy
    else:        # 15% jumper
        return JumperEnemy


def spawn_enemy_far_from_player(min_distance=200):
    """Spawn enemies at least min_distance away from the player."""
    while True:
        x = random.randint(150, WIDTH - 150)
        y = random.randint(150, HEIGHT - 150)
        dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        if dist > min_distance:
            enemy_type = spawn_enemy_type()
            return enemy_type(x, y)


# Wave system
wave = 1
enemies_to_spawn = []


def prepare_wave():
    global enemies_to_spawn
    enemies_to_spawn = []
    base = 1
    total_enemies = base + (wave - 1)
    for _ in range(total_enemies):
        enemies_to_spawn.append(spawn_enemy_far_from_player())


prepare_wave()

# Score + Fonts
score = 0
font = pygame.font.SysFont(None, 36)
pause_font = pygame.font.SysFont(None, 72)

paused = False
game_over = False

# --- Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not game_over:
                paused = not paused
            if game_over and event.key == pygame.K_r:
                # Reset game
                wave = 1
                score = 0
                game_over = False
                player.health = player.PLAYER_MAX_HEALTH
                enemy_group.empty()
                enemy_projectiles.empty()
                prepare_wave()

    if not paused and not game_over:
        keys = pygame.key.get_pressed()

        # Crossbow shooting
        if player.can_attack():
            if keys[pygame.K_UP]:
                projectile_group.add(player.attack('up'))
            elif keys[pygame.K_DOWN]:
                projectile_group.add(player.attack('down'))
            elif keys[pygame.K_LEFT]:
                projectile_group.add(player.attack('left'))
            elif keys[pygame.K_RIGHT]:
                projectile_group.add(player.attack('right'))

        # Update
        player_group.update(walls, keys)
        projectile_group.update(walls)
        particle_group.update()
        enemy_projectiles.update(walls)

        # Enemy updates
        for enemy in list(enemy_group):
            result = enemy.update(player)
            if isinstance(result, pygame.sprite.Sprite):
                enemy_projectiles.add(result)

        # Collisions
        for enemy in enemy_group:
            if player.rect.colliderect(enemy.rect):
                if player.health > 0:
                    player.health -= 1
                dx = player.rect.centerx - enemy.rect.centerx
                dy = player.rect.centery - enemy.rect.centery
                dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
                player.rect.x += int(20 * dx / dist)
                player.rect.y += int(20 * dy / dist)

        for proj in projectile_group:
            hit_enemies = pygame.sprite.spritecollide(proj, enemy_group, False)
            for enemy in hit_enemies:
                proj.kill()
                if enemy.take_hit():
                    enemy.kill()
                    score += 1
                    for _ in range(6):
                        particle_group.add(Particle(proj.rect.centerx, proj.rect.centery))

        for ep in enemy_projectiles:
            if player.rect.colliderect(ep.rect):
                ep.kill()
                if player.health > 0:
                    player.health -= 1

        # Next wave?
        if not enemy_group and not enemies_to_spawn:
            wave += 1
            prepare_wave()

        # Spawn remaining enemies into group
        while enemies_to_spawn:
            enemy_group.add(enemies_to_spawn.pop())

        if player.health <= 0:
            game_over = True

    # --- Drawing ---
    screen.fill(Grey)
    walls.draw(screen)
    player_group.draw(screen)
    projectile_group.draw(screen)
    enemy_group.draw(screen)
    particle_group.draw(screen)
    enemy_projectiles.draw(screen)

    # Health bar
    bar_x, bar_y = 10, 10
    bar_width, bar_height = 150, 20
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (bar_x, bar_y, bar_width, bar_height))
    health_width = int(bar_width * (player.health / player.PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (bar_x, bar_y, health_width, bar_height))

    # Score + Wave
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    wave_text = font.render(f"Wave: {wave}", True, (0, 0, 0))
    screen.blit(score_text, (10, 40))
    screen.blit(wave_text, (10, 70))

    if paused and not game_over:
        pause_text = pause_font.render("PAUSED", True, WHITE)
        rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(pause_text, rect)

    if game_over:
        over_text = pause_font.render("GAME OVER", True, (255, 0, 0))
        rect = over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(over_text, rect)
        instr_text = font.render("Press R to Restart", True, WHITE)
        rect2 = instr_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        screen.blit(instr_text, rect2)

    pygame.display.flip()
    clock.tick(FPS)
