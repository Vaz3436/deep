import pygame
import math
import random

# --- Constants ---
PLAYER_SPEED = 4
PLAYER_RADIUS = 20

PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # ms

ENEMY_SIZE = 30
ENEMY_COLOR = (255, 0, 0)
ENEMY_SPEED = 2

# --- Colors ---
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)


class Player(pygame.sprite.Sprite):
    PLAYER_MAX_HEALTH = 5

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))

        # floating pos for smooth movement of any sub-pixels
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        self.last_shot_time = 0
        self.health = self.PLAYER_MAX_HEALTH
        self.multi_shot_level = 1  # 1, 3, 9, 27, ...

    def update(self, walls, keys):
        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dy = -PLAYER_SPEED
        if keys[pygame.K_s]:
            dy = PLAYER_SPEED
        if keys[pygame.K_a]:
            dx = -PLAYER_SPEED
        if keys[pygame.K_d]:
            dx = PLAYER_SPEED

        # move and collide with walls
        self.pos_x += dx
        self.rect.centerx = int(self.pos_x)
        if pygame.sprite.spritecollide(self, walls, False):
            self.pos_x -= dx
            self.rect.centerx = int(self.pos_x)

        self.pos_y += dy
        self.rect.centery = int(self.pos_y)
        if pygame.sprite.spritecollide(self, walls, False):
            self.pos_y -= dy
            self.rect.centery = int(self.pos_y)

    def can_attack(self):
        return pygame.time.get_ticks() - self.last_shot_time > SHOOT_COOLDOWN

    def attack(self, direction):
        """
        Returns a list of Projectile objects for this attack.
        direction: 'up', 'down', 'left', 'right'
        Multi-shot level determines how many pellets are fired (1, 3, 9, ...).
        Spread is fixed small cone (so more pellets = tighter cluster).
        """
        self.last_shot_time = pygame.time.get_ticks()

        if direction == "up":
            base_angle = -90.0
        elif direction == "down":
            base_angle = 90.0
        elif direction == "left":
            base_angle = 180.0
        else:  # right
            base_angle = 0.0

        num_shots = int(self.multi_shot_level)
        projectiles = []

        # small fixed cone in degrees
        cone_degrees = 18.0

        if num_shots <= 1:
            projectiles.append(Projectile(self.rect.centerx, self.rect.centery, base_angle))
        else:
            # spread the pellets inside the cone. As num_shots grows, step becomes smaller -> tighter pack.
            start = base_angle - (cone_degrees / 2.0)
            step = cone_degrees / (num_shots - 1)
            for i in range(num_shots):
                angle = start + step * i
                projectiles.append(Projectile(self.rect.centerx, self.rect.centery, angle))

        return projectiles


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_degrees):
        super().__init__()
        # small rectangular projectile, rotated to match angle
        base_w, base_h = 14, 4
        base = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        pygame.draw.rect(base, YELLOW, (0, 0, base_w, base_h))
        # rotate so sprite visually matches trajectory
        self.image = pygame.transform.rotate(base, -angle_degrees)
        self.rect = self.image.get_rect(center=(x, y))

        # float positions for smooth movement
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        rad = math.radians(angle_degrees)
        self.dx = PROJECTILE_SPEED * math.cos(rad)
        self.dy = PROJECTILE_SPEED * math.sin(rad)

        self.fly_time = 45  # frames
        self.age = 0

    def update(self, walls=None):
        self.age += 1
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
            return

        if self.age >= self.fly_time:
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
        # flashing visual when hit
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill(self.original_color)

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = max(1.0, math.hypot(dx, dy))
        self.rect.x += int(ENEMY_SPEED * dx / dist)
        self.rect.y += int(ENEMY_SPEED * dy / dist)

        # base enemy doesn't shoot; returns None
        return None

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
        # move like a normal enemy
        super().update(player)
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            # return a projectile aimed at player
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
            dist = max(1.0, math.hypot(dx, dy))
            speed = 6
            self.rect.x += int(speed * dx / dist)
            self.rect.y += int(speed * dy / dist)
            if abs(dx) < 10 and abs(dy) < 10:
                self.target = None
        return None


class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 150, 0))
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        dx = player.rect.centerx - x
        dy = player.rect.centery - y
        dist = max(1.0, math.hypot(dx, dy))
        speed = 5.0
        self.dx = speed * dx / dist
        self.dy = speed * dy / dist

    def update(self, walls=None):
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
