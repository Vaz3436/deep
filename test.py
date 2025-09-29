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

font = pygame.font.SysFont(None, 36)
pause_font = pygame.font.SysFont(None, 72)


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


# --- PowerUp ---
class PowerUp(pygame.sprite.Sprite):
    TYPES = ["health", "multi", "speed", "rapid", "pierce", "explosive"]

    def __init__(self, x, y, kind=None):
        super().__init__()
        self.type = kind if kind is not None else random.choice(PowerUp.TYPES)
        self.image = pygame.Surface((20, 20))
        cmap = {
            "health": (0, 255, 0),
            "multi": (0, 200, 255),
            "speed": (0, 0, 255),
            "rapid": (255, 255, 0),
            "pierce": (255, 100, 0),
            "explosive": (200, 0, 200)
        }
        self.image.fill(cmap.get(self.type, (255, 255, 255)))
        self.rect = self.image.get_rect(center=(x, y))
        self.timer = 15 * FPS

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()


# --- Create Game Objects ---
player = Player(WIDTH // 2, HEIGHT // 2)
player_group = pygame.sprite.GroupSingle(player)
projectile_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemy_projectiles = pygame.sprite.Group()
particle_group = pygame.sprite.Group()
powerup_group = pygame.sprite.Group()

# Walls (keep player away from edges)
walls = pygame.sprite.Group()
walls.add(Wall(0, 0, WIDTH, 100))               # Top
walls.add(Wall(0, HEIGHT - 100, WIDTH, 100))    # Bottom
walls.add(Wall(0, 0, 100, HEIGHT))              # Left
walls.add(Wall(WIDTH - 100, 0, 100, HEIGHT))    # Right


# --- Enemy Spawning Utilities ---
def spawn_enemy_type():
    r = random.random()
    if r < 0.6:
        return Enemy
    elif r < 0.85:
        return ShooterEnemy
    else:
        return JumperEnemy


def spawn_enemy_far_from_player(min_distance=200):
    """Pick a random point inside the arena but at least min_distance from the player."""
    for _ in range(500):
        x = random.randint(120, WIDTH - 120)
        y = random.randint(120, HEIGHT - 120)
        dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        if dist > min_distance:
            E = spawn_enemy_type()
            return E(x, y)
    # fallback
    E = spawn_enemy_type()
    return E(120, 120)


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

# Score + state
score = 0
paused = False
game_over = False


def spawn_powerup_near_center(min_distance_from_player=150):
    for _ in range(200):
        x = random.randint(120, WIDTH - 120)
        y = random.randint(120, HEIGHT - 120)
        dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        if dist > min_distance_from_player:
            pu = PowerUp(x, y)
            powerup_group.add(pu)
            return
    # fallback
    pu = PowerUp(WIDTH // 2, HEIGHT // 2)
    powerup_group.add(pu)


# --- Main Game Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not game_over:
                paused = not paused

            # Restart after game over: reset and teleport to center
            if game_over and event.key == pygame.K_r:
                wave = 1
                score = 0
                game_over = False
                player.health = player.PLAYER_MAX_HEALTH
                player.multi_shot_level = 1
                player.speed_level = 0
                player.rapid_level = 0
                player.piercing_level = 0
                player.explosive_level = 0
                player.last_shot_time = 0
                enemy_group.empty()
                enemy_projectiles.empty()
                projectile_group.empty()
                particle_group.empty()
                powerup_group.empty()
                prepare_wave()
                player.rect.center = (WIDTH // 2, HEIGHT // 2)
                player.pos_x = float(player.rect.centerx)
                player.pos_y = float(player.rect.centery)

    if not paused and not game_over:
        keys = pygame.key.get_pressed()

        # Shooting (use arrow keys). hold to shoot with cooldown.
        if player.can_attack():
            direction = None
            if keys[pygame.K_UP]:
                direction = "up"
            elif keys[pygame.K_DOWN]:
                direction = "down"
            elif keys[pygame.K_LEFT]:
                direction = "left"
            elif keys[pygame.K_RIGHT]:
                direction = "right"

            if direction:
                pellets = player.attack(direction)
                for p in pellets:
                    projectile_group.add(p)

        # Update groups (pass walls/keys where needed)
        player_group.update(walls, keys)
        projectile_group.update(walls)
        enemy_projectiles.update(walls)
        particle_group.update()
        powerup_group.update()

        # Enemy updates (some enemies may return a projectile to spawn)
        for enemy in list(enemy_group):
            result = enemy.update(player)
            if isinstance(result, pygame.sprite.Sprite):
                enemy_projectiles.add(result)

        # Collisions: player <-> enemies (touch damage + knockback)
        for enemy in list(enemy_group):
            if player.rect.colliderect(enemy.rect):
                if player.health > 0:
                    player.health -= 1
                dx = player.rect.centerx - enemy.rect.centerx
                dy = player.rect.centery - enemy.rect.centery
                dist = max(1.0, (dx ** 2 + dy ** 2) ** 0.5)
                player.pos_x += 20 * dx / dist
                player.pos_y += 20 * dy / dist
                player.rect.centerx = int(player.pos_x)
                player.rect.centery = int(player.pos_y)

        # Projectile hits enemies (supports piercing and explosive)
        for proj in list(projectile_group):
            hits = pygame.sprite.spritecollide(proj, enemy_group, False)
            if hits:
                # explosive projectiles explode on first hit
                if getattr(proj, "explosive", 0) and proj.explosive > 0:
                    radius = 30 + 10 * proj.explosive
                    cx, cy = proj.rect.center
                    for enemy in list(enemy_group):
                        ex, ey = enemy.rect.center
                        if ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5 <= radius:
                            if enemy.take_hit():
                                enemy.kill()
                                score += 1
                                for _ in range(6):
                                    particle_group.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                    proj.kill()
                    continue

                # normal/piercing handling
                for enemy in hits:
                    if getattr(proj, "hits_left", 1) > 0:
                        if enemy.take_hit():
                            enemy.kill()
                            score += 1
                            for _ in range(6):
                                particle_group.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                        proj.hits_left -= 1
                    if proj.hits_left <= 0:
                        proj.kill()
                        break

        # Enemy projectiles hit player
        for ep in list(enemy_projectiles):
            if player.rect.colliderect(ep.rect):
                ep.kill()
                if player.health > 0:
                    player.health -= 1

        # Power-up pickup
        collected = pygame.sprite.spritecollide(player, powerup_group, True)
        for pu in collected:
            if pu.type == "health":
                player.health = min(player.PLAYER_MAX_HEALTH, player.health + 2)
            elif pu.type == "multi":
                # multiply pellet count: 1 -> 3 -> 9 -> 27 ...
                player.multi_shot_level = int(player.multi_shot_level * 3)
            elif pu.type == "speed":
                player.speed_level += 1
            elif pu.type == "rapid":
                player.rapid_level += 1
            elif pu.type == "pierce":
                player.piercing_level += 1
            elif pu.type == "explosive":
                player.explosive_level += 1

        # Next wave?
        if not enemy_group and not enemies_to_spawn:
            wave += 1
            prepare_wave()

            # spawn a power-up every 5th wave (on waves 5,10,15,...)
            if wave % 5 == 0:
                spawn_powerup_near_center()

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
    powerup_group.draw(screen)

    # Health bar
    bar_x, bar_y = 10, 10
    bar_width, bar_height = 150, 20
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (bar_x, bar_y, bar_width, bar_height))
    health_width = int(bar_width * (player.health / player.PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (bar_x, bar_y, health_width, bar_height))

    # Score + Wave + HP
    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    wave_text = font.render(f"Wave: {wave}", True, (0, 0, 0))
    hp_text = font.render(f"HP: {player.health}", True, (0, 0, 0))
    screen.blit(score_text, (10, 40))
    screen.blit(wave_text, (10, 70))
    screen.blit(hp_text, (10, 100))

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
