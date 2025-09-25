import pygame
import random
import math

# --- Constants ---
PLAYER_SPEED = 4
PLAYER_RADIUS = 20

PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # ms

ENEMY_SIZE = 30
ENEMY_COLOR = (255, 0, 0)

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
        # keep float pos for smooth movement and to avoid truncation issues
        self.pos = [float(x), float(y)]
        self.last_shot_time = 0
        self.health = self.PLAYER_MAX_HEALTH

    def update(self, walls, keys):
        dx, dy = 0.0, 0.0
        if keys[pygame.K_w]: dy = -PLAYER_SPEED
        if keys[pygame.K_s]: dy = PLAYER_SPEED
        if keys[pygame.K_a]: dx = -PLAYER_SPEED
        if keys[pygame.K_d]: dx = PLAYER_SPEED

        # move X then Y with wall collision rollback
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
    def __init__(self, x, y, direction, speed=PROJECTILE_SPEED, color=YELLOW):
        super().__init__()
        self.direction = direction
        if direction in ("left", "right"):
            self.image = pygame.Surface((25, 4))
        else:
            self.image = pygame.Surface((4, 25))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = [float(x), float(y)]
        self.speed = speed
        self.dx = 0.0
        self.dy = 0.0
        if direction == "up":
            self.dy = -self.speed
        elif direction == "down":
            self.dy = self.speed
        elif direction == "left":
            self.dx = -self.speed
        elif direction == "right":
            self.dx = self.speed

        self.fly_time = 45  # frames
        self.age = 0

    def update(self, walls=None):
        self.age += 1
        self.pos[0] += self.dx
        self.pos[1] += self.dy
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])

        # remove if hit walls
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
            return

        # lifetime end
        if self.age >= self.fly_time:
            self.kill()


# ---------------- Enemies ----------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, health=2, color=ENEMY_COLOR, speed=ENEMY_SIZE / 15):
        super().__init__()
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.original_color = color
        self.flash_color = (255, 255, 0)
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = [float(x), float(y)]
        self.health = health
        self.flash_timer = 0
        # default speed (float)
        self.speed = float(speed)

    def _handle_flash(self):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill(self.original_color)

    def update(self, player, walls=None, playable_rect=None, projectile_group=None):
        # handle flash color decay
        self._handle_flash()

        # movement toward player using float pos
        dx = player.rect.centerx - self.pos[0]
        dy = player.rect.centery - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist == 0:
            return None
        nx = dx / dist
        ny = dy / dist

        old_pos = (self.pos[0], self.pos[1])
        self.pos[0] += nx * self.speed
        self.pos[1] += ny * self.speed
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])

        # collision with walls -> rollback to old_pos
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.pos[0], self.pos[1] = old_pos
            self.rect.centerx = int(self.pos[0])
            self.rect.centery = int(self.pos[1])

        # clamp inside playable rect if given
        if playable_rect:
            # rect.clamp_ip expects ints; ensure pos & rect sync
            self.rect.clamp_ip(playable_rect)
            self.pos[0], self.pos[1] = float(self.rect.centerx), float(self.rect.centery)

        return None

    def take_hit(self):
        self.health -= 1
        self.image.fill(self.flash_color)
        self.flash_timer = 15  # frames
        return self.health <= 0


class TankEnemy(Enemy):
    def __init__(self, x, y):
        # slow and tanky
        super().__init__(x, y, health=6, color=(120, 50, 50), speed=0.9)


class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, color=(255, 120, 0)):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = [float(x), float(y)]
        self.vx = float(vx)
        self.vy = float(vy)

    def update(self, walls=None, playable_rect=None):
        self.pos[0] += self.vx
        self.pos[1] += self.vy
        self.rect.centerx = int(self.pos[0])
        self.rect.centery = int(self.pos[1])
        # die on wall hit
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
            return
        # optional: kill if outside playable_rect (if provided)
        if playable_rect and not playable_rect.collidepoint(self.rect.center):
            self.kill()


class ShooterEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, health=3, color=(50, 140, 50), speed=1.2)
        self.shoot_cooldown_ms = 1200
        self.last_shot = pygame.time.get_ticks() - random.randint(0, self.shoot_cooldown_ms)

    def update(self, player, walls=None, playable_rect=None, projectile_group=None):
        # move like base enemy
        super().update(player, walls, playable_rect, projectile_group)

        # shooting toward player using projectile_group if provided
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
        # drift speed small, dash occasionally
        super().__init__(x, y, health=2, color=(50, 50, 150), speed=0.45)
        self.dash_cooldown_ms = random.randint(1200, 2200)
        self.last_dash_time = pygame.time.get_ticks() - random.randint(0, self.dash_cooldown_ms)
        self.dashing = False
        self.dash_vx = 0.0
        self.dash_vy = 0.0
        self.dash_target = None
        self.dash_speed = 6.0
        self.dash_max_distance = 90.0

    def update(self, player, walls=None, playable_rect=None, projectile_group=None):
        # flash handling
        self._handle_flash()

        now = pygame.time.get_ticks()
        if self.dashing:
            # move toward dash_target using dash_vx/dash_vy
            old_pos = (self.pos[0], self.pos[1])
            self.pos[0] += self.dash_vx
            self.pos[1] += self.dash_vy
            self.rect.centerx = int(self.pos[0])
            self.rect.centery = int(self.pos[1])

            # if wall collision, rollback and stop dash
            if walls and pygame.sprite.spritecollideany(self, walls):
                self.pos[0], self.pos[1] = old_pos
                self.rect.centerx = int(self.pos[0])
                self.rect.centery = int(self.pos[1])
                self.dashing = False
                self.last_dash_time = now
                return None

            # if reached or passed target (distance)
            dx_remain = self.dash_target[0] - self.pos[0]
            dy_remain = self.dash_target[1] - self.pos[1]
            if math.hypot(dx_remain, dy_remain) <= self.dash_speed:
                # snap to target and stop
                self.pos[0], self.pos[1] = float(self.dash_target[0]), float(self.dash_target[1])
                self.rect.centerx = int(self.pos[0])
                self.rect.centery = int(self.pos[1])
                self.dashing = False
                self.last_dash_time = now
        else:
            # gentle follow/drift toward player
            dx = player.rect.centerx - self.pos[0]
            dy = player.rect.centery - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist != 0:
                nx = dx / dist
                ny = dy / dist
                old_pos = (self.pos[0], self.pos[1])
                self.pos[0] += nx * self.speed
                self.pos[1] += ny * self.speed
                self.rect.centerx = int(self.pos[0])
                self.rect.centery = int(self.pos[1])
                if walls and pygame.sprite.spritecollideany(self, walls):
                    self.pos[0], self.pos[1] = old_pos
                    self.rect.centerx = int(self.pos[0])
                    self.rect.centery = int(self.pos[1])

            # time to dash?
            if now - self.last_dash_time >= self.dash_cooldown_ms:
                dx = player.rect.centerx - self.pos[0]
                dy = player.rect.centery - self.pos[1]
                dist = math.hypot(dx, dy)
                if dist == 0:
                    return None
                take = min(self.dash_max_distance, dist)
                tx = self.pos[0] + (dx / dist) * take
                ty = self.pos[1] + (dy / dist) * take

                # clamp target to playable_rect if provided
                if playable_rect:
                    tx = max(playable_rect.left + self.rect.width // 2, min(tx, playable_rect.right - self.rect.width // 2))
                    ty = max(playable_rect.top + self.rect.height // 2, min(ty, playable_rect.bottom - self.rect.height // 2))

                self.dash_target = (tx, ty)
                # compute dash vx/vy (per-frame)
                dx_t = tx - self.pos[0]
                dy_t = ty - self.pos[1]
                dist_t = math.hypot(dx_t, dy_t)
                if dist_t != 0:
                    self.dash_vx = (dx_t / dist_t) * self.dash_speed
                    self.dash_vy = (dy_t / dist_t) * self.dash_speed
                    self.dashing = True
                    # set next cooldown earlier so dash happens periodically
                    self.last_dash_time = now
                    self.dash_cooldown_ms = random.randint(1200, 2200)

        # safety clamp to playable rect
        if playable_rect:
            self.rect.clamp_ip(playable_rect)
            self.pos[0], self.pos[1] = float(self.rect.centerx), float(self.rect.centery)

        return None
