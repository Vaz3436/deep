import pygame
import random

# --- Constants ---
PLAYER_SPEED = 4
PLAYER_RADIUS = 20

PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # milliseconds

ENEMY_SIZE = 30
ENEMY_COLOR = (255, 0, 0)
ENEMY_SPEED = 2

# --- Colors ---
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
STUCK_ARROW_COLOR = (180, 180, 60)


class Player(pygame.sprite.Sprite):
    PLAYER_MAX_HEALTH = 5

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))
        self.last_shot_time = 0
        self.health = self.PLAYER_MAX_HEALTH

    def update(self, walls, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy = -PLAYER_SPEED
        if keys[pygame.K_s]: dy = PLAYER_SPEED
        if keys[pygame.K_a]: dx = -PLAYER_SPEED
        if keys[pygame.K_d]: dx = PLAYER_SPEED

        self.rect.x += dx
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x -= dx

        self.rect.y += dy
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.y -= dy

    def can_attack(self):
        return pygame.time.get_ticks() - self.last_shot_time > SHOOT_COOLDOWN

    def attack(self, direction):
        self.last_shot_time = pygame.time.get_ticks()
        return Projectile(self.rect.centerx, self.rect.centery, direction)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.direction = direction
        if direction in ['left', 'right']:
            self.image = pygame.Surface((25, 4))
        else:
            self.image = pygame.Surface((4, 25))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))

        self.dx, self.dy = 0, 0
        if direction == 'up': self.dy = -PROJECTILE_SPEED
        elif direction == 'down': self.dy = PROJECTILE_SPEED
        elif direction == 'left': self.dx = -PROJECTILE_SPEED
        elif direction == 'right': self.dx = PROJECTILE_SPEED

        self.fly_time = 45
        self.age = 0
        self.landed = False
        self.stuck = False

    def update(self, walls=None):
        self.age += 1
        if not self.stuck:
            self.rect.x += self.dx
            self.rect.y += self.dy

            if walls and pygame.sprite.spritecollideany(self, walls):
                self.dx = self.dy = 0
                self.stuck = True
                self.image.fill(STUCK_ARROW_COLOR)
                return

            if self.age >= self.fly_time:
                self.dx = self.dy = 0
                self.landed = True
                self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.original_color = ENEMY_COLOR
        self.flash_color = (255, 255, 0)
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 2
        self.flash_timer = 0

    def update(self, player):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill(self.original_color)

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        self.rect.x += int(ENEMY_SPEED * dx / dist)
        self.rect.y += int(ENEMY_SPEED * dy / dist)

    def take_hit(self):
        self.health -= 1
        self.image.fill(self.flash_color)
        self.flash_timer = 15
        return self.health <= 0


class ShooterEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((200, 50, 200))
        self.shoot_cooldown = 90
        self.timer = 0

    def update(self, player):
        super().update(player)
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            return EnemyProjectile(self.rect.centerx, self.rect.centery, player)
        return None


class JumperEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((50, 200, 50))
        self.jump_cooldown = random.randint(120, 180)
        self.timer = 0
        self.target = None

    def update(self, player):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill((50, 200, 50))

        self.timer += 1
        if self.timer >= self.jump_cooldown:
            self.timer = 0
            self.jump_cooldown = random.randint(120, 180)
            self.target = player.rect.center

        if self.target:
            dx = self.target[0] - self.rect.centerx
            dy = self.target[1] - self.rect.centery
            dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
            speed = 6
            self.rect.x += int(speed * dx / dist)
            self.rect.y += int(speed * dy / dist)
            if abs(dx) < 10 and abs(dy) < 10:
                self.target = None


class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 150, 0))
        self.rect = self.image.get_rect(center=(x, y))
        dx = player.rect.centerx - x
        dy = player.rect.centery - y
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        speed = 5
        self.dx = speed * dx / dist
        self.dy = speed * dy / dist

    def update(self, walls=None):
        self.rect.x += int(self.dx)
        self.rect.y += int(self.dy)
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
