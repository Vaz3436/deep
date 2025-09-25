import pygame
import random
import math

# --- Constants ---
PLAYER_SPEED = 4.0
PLAYER_RADIUS = 20

PROJECTILE_SPEED = 8.0
SHOOT_COOLDOWN = 300  # ms

ENEMY_SIZE = 30
ENEMY_BASE_SPEED = 1.6

# --- Colors ---
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ENEMY_COLOR = (255, 0, 0)


class Player(pygame.sprite.Sprite):
    PLAYER_MAX_HEALTH = 5

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))
        # keep float pos for smooth movement
        self.pos = [float(self.rect.centerx), float(self.rect.centery)]
        self.last_shot_time = 0
        self.health = self.PLAYER_MAX_HEALTH

    def update(self, walls, keys):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w]:
            dy = -PLAYER_SPEED
        if keys[pygame.K_s]:
            dy = PLAYER_SPEED
        if keys[pygame.K_a]:
            dx = -PLAYER_SPEED
        if keys[pygame.K_d]:
            dx = PLAYER_SPEED

        # move X then Y with wall rollback
        old_x = self.pos[0]
        self.pos[0] += dx
        self.rect.centerx = int(self.pos[0])
        if walls and pygame.sprite.spritecollide(self, walls, False):
            self.pos[0] = old_x
            self.rect.centerx = int(self.pos[0])

        old_y = self.pos[1]
        self.pos[1] += dy
        self.rect.centery = int(self.pos[1])
        if walls and pygame.sprite.spritecollide(self, walls, False):
            self.pos[1] = old_y
            self.rect.centery = int(self.pos[1])

    def can_attack(self):
        return pygame.time.get_ticks() - self.last_shot_time > SHOOT_COOLDOWN

    def attack(self, direction):
        self.last_shot_time = pygame.time.get_ticks()
        return Projectile(self.rect.centerx, self.rect.centery, direction)


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, speed=PROJECTILE_SPEED, lifetime=90):
        super().__init__()
        self.direction = direction
        if direction in ("left", "right"):
            self.image = pygame.Surface((25, 4))
        else:
            self.image = pygame.Surface((4, 25))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = [float(x), float(y)]
        self.speed = float(speed)
        self.vx = 0.0
        self.vy = 0.0
        if direction == "up":
            self.vy = -self.speed
        elif direction == "down":
            self.vy = self.speed
        elif direction == "left":
            self.vx = -self.speed
        elif direction == "right":
            self.vx = self.speed

        self.age = 0
        self.lifetime = lifetime

    def update(self, walls=None, playable_rect=None):
        self.age += 1
        self.pos[0] += self.vx
        self.pos[1] += self.vy
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])

        # vanish on wall hit
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
            return

        # vanish when leaving playable_rect (optional)
        if playable_rect and not playable_rect.collidepoint(self.rect.center):
            self.kill()
            return

        if self.age >= self.lifetime:
            self.kill()


# ---------------- Enemies ----------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health=2, color=ENEMY_COLOR, speed=ENEMY_BASE_SPEED):
        super().__init__()
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.original_color = color
        self.flash_color = (255, 255, 0)
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = [float(self.rect.centerx), float(self.rect.centery)]
        self.health = health
        self.flash_timer = 0
        self.speed = float(speed)

    def _handle_flash(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill(self.original_color)

    def update(self, player, walls=None, playable_rect=None, projectile_group=None):
        # flash decay
        self._handle_flash()

        # move toward player with float pos and rollback on wall collision
        dx = player.rect.centerx - self.pos[0]
        dy = player.rect.centery - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return None
        nx = dx / dist
        ny = dy / dist

        old = (self.pos[0], self.pos[1])
        self.pos[0] += nx * self.speed
        self.pos[1] += ny * self.speed
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])

        if walls and pygame.sprite.spritecollideany(self, walls):
            self.pos[0], self.pos[1] = old
            self.rect.centerx = int(self.pos[0])
            self.rect.centery = int(self.pos[1])

        if playable_rect:
            # clamp pos to playable area to be safe
            self.rect.clamp_ip(playable_rect)
            self.pos[0], self.pos[1] = float(self.rect.centerx), float(self.rect.centery)

        return None

    def take_hit(self):
        self.health -= 1
        self.image.fill(self.flash_color)
        self.flash_timer = 15
        return self.health <= 0


class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, color=(255, 120, 0), lifetime=300):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.pos = [float(x), float(y)]
        self.vx = float(vx)
        self.vy = float(vy)
        self.age = 0
        self.lifetime = lifetime

    def update(self, walls=None, playable_rect=None):
        self.age += 1
        self.pos[0] += self.vx
        self.pos[1] += self.vy
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])

        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
            return

        if playable_rect and not playable_rect.collidepoint(self.rect.center):
            self.kill()
            return

        if self.age >= self.lifetime:
            self.kill()


class ShooterEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=3, color=(50, 140, 50), speed=1.2)
        self.shoot_cooldown_ms = 1200
        self.last_shot = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown_ms)

    def update(self, player, walls=None, playable_rect=None, projectile_group=None):
        # move
        super().update(player, walls, playable_rect, projectile_group)

        # shoot periodically (if group provided)
        if projectile_group is not None:
            now = pygame.time.get_ticks()
            if now - self.last_shot >= self.shoot_cooldown_ms:
                self.last_shot = now
                dx = player.rect.centerx - self.pos[0]
                dy = player.rect.centery - self.pos[1]
                dist = math.hypot(dx, dy)
                if dist == 0:
                    return None
                speed = 4.0
                vx = (dx / dist) * speed
                vy = (dy / dist) * speed
                proj = EnemyProjectile(self.pos[0], self.pos[1], vx, vy)
                projectile_group.add(proj)
        return None


class JumperEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=2, color=(70, 70, 160), speed=0.5)
        self.dash_cooldown_ms = random.randint(1200, 2200)
        self.last_dash = pygame.time.get_ticks() - random.randint(0, self.dash_cooldown_ms)
        self.dashing = False
        self.dash_vx = 0.0
        self.dash_vy = 0.0
        self.dash_target = None
        self.dash_speed = 6.0
        self.dash_max_distance = 80.0

    def update(self, player, walls=None, playable_rect=None, projectile_group=None):
        # flash
        self._handle_flash()
        now = pygame.time.get_ticks()

        if self.dashing:
            # apply dash velocity
            old = (self.pos[0], self.pos[1])
            self.pos[0] += self.dash_vx
            self.pos[1] += self.dash_vy
            self.rect.centerx = int(self.pos[0])
            self.rect.centery = int(self.pos[1])

            # wall collision - rollback and stop dash
            if walls and pygame.sprite.spritecollideany(self, walls):
                self.pos[0], self.pos[1] = old
                self.rect.centerx = int(self.pos[0])
                self.rect.centery = int(self.pos[1])
                self.dashing = False
                self.last_dash = now
                return None

            # reached target?
            if self.dash_target:
                dxr = self.dash_target[0] - self.pos[0]
                dyr = self.dash_target[1] - self.pos[1]
                if math.hypot(dxr, dyr) <= self.dash_speed:
                    self.pos[0], self.pos[1] = float(self.dash_target[0]), float(self.dash_target[1])
                    self.rect.centerx = int(self.pos[0])
                    self.rect.centery = int(self.pos[1])
                    self.dashing = False
                    self.last_dash = now
        else:
            # gentle follow
            dx = player.rect.centerx - self.pos[0]
            dy = player.rect.centery - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist != 0:
                nx = dx / dist
                ny = dy / dist
                old = (self.pos[0], self.pos[1])
                self.pos[0] += nx * self.speed
                self.pos[1] += ny * self.speed
                self.rect.centerx = int(self.pos[0])
                self.rect.centery = int(self.pos[1])
                if walls and pygame.sprite.spritecollideany(self, walls):
                    self.pos[0], self.pos[1] = old
                    self.rect.centerx = int(self.pos[0])
                    self.rect.centery = int(self.pos[1])

            # possibly start dash
            if now - self.last_dash >= self.dash_cooldown_ms:
                dx = player.rect.centerx - self.pos[0]
                dy = player.rect.centery - self.pos[1]
                dist = math.hypot(dx, dy)
                if dist == 0:
                    return None
                take = min(self.dash_max_distance, dist)
                tx = self.pos[0] + (dx / dist) * take
                ty = self.pos[1] + (dy / dist) * take

                if playable_rect:
                    tx = max(playable_rect.left + self.rect.width // 2, min(tx, playable_rect.right - self.rect.width // 2))
                    ty = max(playable_rect.top + self.rect.height // 2, min(ty, playable_rect.bottom - self.rect.height // 2))

                self.dash_target = (tx, ty)
                # compute per-frame dash vx/vy
                dx_t = tx - self.pos[0]
                dy_t = ty - self.pos[1]
                dist_t = math.hypot(dx_t, dy_t)
                if dist_t != 0:
                    self.dash_vx = (dx_t / dist_t) * self.dash_speed
                    self.dash_vy = (dy_t / dist_t) * self.dash_speed
                    self.dashing = True
                    self.last_dash = now
                    self.dash_cooldown_ms = random.randint(1200, 2200)

        # final clamp
        if playable_rect:
            self.rect.clamp_ip(playable_rect)
            self.pos[0], self.pos[1] = float(self.rect.centerx), float(self.rect.centery)

        return None
