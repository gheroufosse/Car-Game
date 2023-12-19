# Initialization ----------------------------------------------------------------

from typing import AbstractSet
import pygame
import time
import math
import os
from utils import scale_image, blit_rotate_center, blit_text_center

pygame.font.init()

MAIN_FONT = pygame.font.SysFont("comic_sans", 42)

# Various import of the game object

GRASS = scale_image(pygame.image.load(os.path.join("imgs", "grass.jpg")), 2.5)
TRACK = scale_image(pygame.image.load(os.path.join("imgs", "track.png")), 0.8)

TRACK_BORDER = scale_image(
    pygame.image.load(os.path.join("imgs", "track-border.png")), 0.8
)
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)

FINISH = pygame.image.load(os.path.join("imgs", "finish.png"))
FINISH_MASK = pygame.mask.from_surface(FINISH)
FINISH_POSITION = (115, 230)


RED_CAR = scale_image(pygame.image.load(os.path.join("imgs", "red-car.png")), 0.5)
GREEN_CAR = scale_image(pygame.image.load(os.path.join("imgs", "green-car.png")), 0.5)

WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()

WIN = pygame.display.set_mode((WIDTH, HEIGHT))  # Tuple with the size of the game
pygame.display.set_caption("Racing game")

PATH = [
    (154, 111),
    (74, 74),
    (52, 196),
    (55, 398),
    (87, 470),
    (267, 635),
    (360, 531),
    (365, 467),
    (478, 428),
    (535, 560),
    (539, 623),
    (656, 570),
    (658, 433),
    (659, 378),
    (402, 324),
    (416, 231),
    (609, 231),
    (661, 154),
    (637, 79),
    (377, 60),
    (294, 65),
    (246, 199),
    (247, 336),
    (157, 306),
    (150, 234),
]

WHITE = (255, 255, 255)


class GameInfo:
    LEVELS = 10

    def __init__(self, level=1):
        self.level = level
        self.started = False
        self.level_start_time = 0

    def next_level(self):
        self.level += 1
        self.started = False

    def reset(self):
        self.level = 1
        self.started = False
        self.level_start_time = 0

    def game_finished(self):
        return self.level > self.LEVELS

    def start_level(self):
        self.started = True
        self.level_start_time = time.time()

    def get_level_time(self):
        if not self.started:
            return 0
        return time.time() - self.level_start_time


class AbstractCar:
    def __init__(self, max_velocity, rotation_velocity):
        self.max_vel = max_velocity
        self.vel = 0
        self.rotation_velocity = rotation_velocity
        self.angle = 0
        self.img = self.IMG
        self.x, self.y = self.START_POS
        self.acceleration = 0.08

    def rotate(self, left=False, right=False):
        if left:
            self.angle += self.rotation_velocity
        elif right:
            self.angle -= self.rotation_velocity

    def draw(self, win):
        blit_rotate_center(win, self.img, (self.x, self.y), self.angle)

    def move_forward(self):
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

    def move_backward(self):
        self.vel = max(self.vel - self.acceleration, -self.max_vel / 2)
        self.move()

    def move(self):
        radians = math.radians(self.angle)
        horizontal = self.vel * math.sin(radians)
        vertical = self.vel * math.cos(radians)

        self.x -= horizontal
        self.y -= vertical

    def reduce_speed(self):
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()

    def collide(self, mask, x=0, y=0):
        car_mask = pygame.mask.from_surface(self.img)
        offset = (int(self.x - x), int(self.y - y))
        poi = mask.overlap(car_mask, offset)
        return poi

    def bounce(self):
        self.vel = -self.vel / 2
        self.move()

    def reset(self):
        self.x, self.y = self.START_POS
        self.angle = 0
        self.vel = 0


class ComputerCar(AbstractCar):
    IMG = GREEN_CAR
    START_POS = (135, 190)

    def __init__(self, max_velocity, rotation_velocity, path=[]):
        super().__init__(max_velocity, rotation_velocity)
        self.path = path
        self.current_point = 0
        self.vel = max_velocity

    def draw_points(self, win):
        for point in self.path:
            pygame.draw.circle(win, (255, 0, 0), point, 1.0)

    def draw(self, win):
        super().draw(win)
        # self.draw_points(win)

    def calculate_angle(self):
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            desired_radians_angle = math.pi / 2
        else:
            desired_radians_angle = math.atan(x_diff / y_diff)

        if target_y > self.y:
            desired_radians_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radians_angle)

        if difference_in_angle >= 180:  # Make sure to turn the fastest direction
            difference_in_angle -= 360

        if difference_in_angle > 0:
            self.angle -= min(self.vel, abs(difference_in_angle))
        else:
            self.angle += min(self.vel, abs(difference_in_angle))

    def update_path_points(self):
        target = self.path[self.current_point]
        rect = pygame.Rect(self.x, self.y, self.img.get_width(), self.img.get_height())
        if rect.collidepoint(*target):
            self.current_point += 1

    def move(self):
        if self.current_point >= len(self.path):
            return

        self.calculate_angle()
        self.update_path_points()

        super().move()

    def next_level(self, level):
        self.reset()
        self.vel = self.max_vel + (level - 1) * 0.111
        self.current_point = 0


class PlayerCar(AbstractCar):
    IMG = RED_CAR
    START_POS = (160, 190)


def draw(win, images, player_car, computer_car, game_info):
    for img, pos in images:
        win.blit(img, pos)

    level_text = MAIN_FONT.render(f"Level {game_info.level}", 1, WHITE)
    win.blit(level_text, (10, HEIGHT - level_text.get_height() - 70))

    time_text = MAIN_FONT.render(
        f"Time: {round(game_info.get_level_time(),1)}s", 1, WHITE
    )
    win.blit(time_text, (10, HEIGHT - time_text.get_height() - 40))

    velocity_text = MAIN_FONT.render(
        f"Velocity: {round(player_car.vel,1)}px/s", 1, WHITE
    )
    win.blit(velocity_text, (10, HEIGHT - velocity_text.get_height() - 10))

    player_car.draw(win)
    computer_car.draw(win)
    pygame.display.update()


def move_player(player_car):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_q]:
        player_car.rotate(left=True)
    if keys[pygame.K_d]:
        player_car.rotate(right=True)
    if keys[pygame.K_z]:
        moved = True
        player_car.move_forward()

    if keys[pygame.K_s]:
        moved = True
        player_car.move_backward()

    if not moved:
        player_car.reduce_speed()


def handle_collision(player_car, computer_car, game_info):
    if player_car.collide(TRACK_BORDER_MASK) != None:
        player_car.bounce()

    computer_finish_poi_collide = computer_car.collide(
        FINISH_MASK, *FINISH_POSITION
    )  # * split the tuple of Position to evaluate both values
    if computer_finish_poi_collide != None:
        blit_text_center(WIN, MAIN_FONT, f"You lost!")
        pygame.display.update()
        pygame.time.wait(4500)
        game_info.reset()
        player_car.reset()
        computer_car.next_level(1)

    player_finish_poi_collide = player_car.collide(
        FINISH_MASK, *FINISH_POSITION
    )  # * split the tuple of Position to evaluate both values

    if player_finish_poi_collide != None:
        if player_finish_poi_collide[1] == 0:
            player_car.bounce()
        else:
            game_info.next_level()
            player_car.reset()
            computer_car.next_level(game_info.level)


FPS = 60
clock = pygame.time.Clock()
run = True
images = [
    (GRASS, (0, 0)),
    (TRACK, (0, 0)),
    (FINISH, FINISH_POSITION),
    (TRACK_BORDER, (0, 0)),
]
player_car = PlayerCar(3, 3.5)
computer_car = ComputerCar(2.4, 3.48, PATH)

game_info = GameInfo()

while run:
    clock.tick(FPS)
    draw(WIN, images, player_car, computer_car, game_info)

    while not game_info.started:
        blit_text_center(
            WIN, MAIN_FONT, f"Press any key to start level {game_info.level}!"
        )
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                break
            if event.type == pygame.KEYDOWN:
                game_info.start_level()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
            break

        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            computer_car.path.append(pos)

    move_player(player_car)
    computer_car.move()
    handle_collision(player_car, computer_car, game_info)

    if game_info.game_finished():
        blit_text_center(WIN, MAIN_FONT, f"You won the game !")
        pygame.display.update()
        pygame.time.wait(4500)
        game_info.reset()
        player_car.reset()
        computer_car.reset()

pygame.quit()
