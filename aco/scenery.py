import math
import random
from dataclasses import dataclass

import pygame

from .colours import Colour


class Resource:
    def __init__(self, world_position: pygame.Vector2):
        self.world_position = world_position


@dataclass
class TreeData:
    world_position: tuple[int, int]
    seed: int
    length: int = 150
    main_branch_length: int = 80
    mini_branch_length: int = 40


class Tree(Resource):
    def __init__(self, world_position: pygame.Vector2, magnitude: int = 25):
        super().__init__(world_position=world_position)
        self.screen_x = 0
        self.screen_y = 0
        self.magnitude = magnitude
        self.visual = TreeData(
            world_position=(int(self.world_position.x), int(self.world_position.y)),
            seed=hash((int(self.world_position.x), int(self.world_position.y))))
        """
        have to comment because of my beautifully named variable. Ik.
        created a local seed so.. that it stays local. I already used the
        global seed somewhere
        """
        self.r = random.Random(self.visual.seed)
        # polar
        self.angle = self.r.uniform(0, math.tau)
        self.angular_speed = self.r.uniform(0, math.tau)
        self.radius = self.r.uniform(3, 6)
        self.offset = pygame.Vector2(
            self.r.randint(-250, 250),
            self.r.randint(-250, 250)
        )
        self.offset_length = pygame.Vector2(
            self.r.randint(-20, 20),
            self.r.randint(-20, 20)
        )

    def get_collision_rect(self):
        size = 120
        return pygame.Rect(
            self.world_position.x + self.offset.x - size // 2,
            self.world_position.y + self.offset.y - size // 2,
            size,
            size
        )

    def get_screen_rect(self):
        return pygame.Rect(
            (self.screen_x - TreeData.length // 2),
            (self.screen_y - TreeData.length // 2),
            TreeData.length,
            TreeData.length
        )

    def Draw_tree(self, screen: pygame.Surface, world_offset: pygame.Vector2):
        """The random offset at the end has a purpose. -> its because i generated
        the coord using nodes. so its off-putting when trees align with each other.. by a LOT """
        self.angle += self.angular_speed * (1 / 40)
        if self.angle > math.tau:
            self.angle -= math.tau
        dx = math.cos(self.angle) * self.radius
        dy = math.sin(self.angle) * self.radius
        self.screen_x = (self.world_position.x - world_offset.x) + self.offset.x
        self.screen_y = (self.world_position.y - world_offset.y) + self.offset.y
        length = TreeData.length
        width = TreeData.length
        self.r.seed(hash((self.world_position.x, self.world_position.y)))
        offset_x = self.r.randint(-40, 40)
        offset_y = self.r.randint(-40, 40)
        rect2 = pygame.Rect(
            (self.screen_x - width // 2) + offset_x + dx,
            (self.screen_y - length // 2) + offset_y + dy,
            width - 20,
            length - 20
        )
        rect_ = pygame.Rect(
            (self.screen_x - width // 2),
            (self.screen_y - length // 2),
            width,
            length
        )

        pygame.draw.rect(
            screen,
            Colour.dense_canopy,
            rect_,
            border_radius=20)
        pygame.draw.rect(
            screen,
            Colour.light_canopy,
            rect2,
            border_radius=20
        )

        pygame.draw.rect(
            screen,
            Colour.tree_border,
            rect_,
            width=3,
            border_radius=20
        )


@dataclass
class RockData:
    world_position: tuple[int, int]
    seed: int
    magnitude: int = 100


class Rock(Resource):
    def __init__(self, world_position: pygame.Vector2):
        super().__init__(world_position=world_position)
        self.world_position = world_position
        self.screen_x = 0
        self.screen_y = 0
        self.visual = RockData(
            world_position=(int(self.world_position.x), int(self.world_position.y)),
            seed=hash((int(self.world_position.x), int(self.world_position.y))))
        self.r = random.Random(self.visual.seed)

        self.offset = pygame.Vector2(
            self.r.randint(-250, 250),
            self.r.randint(-250, 250)
        )

        self.offset_x = self.r.randint(-40, 40)
        self.offset_y = self.r.randint(-40, 40)

    def get_screen_rect(self):
        magnitude = RockData.magnitude

        return pygame.Rect(
            (self.screen_x - magnitude // 2),
            (self.screen_y - magnitude // 2),
            magnitude,
            magnitude
        )

    def get_collision_rect(self):
        size = RockData.magnitude

        return pygame.Rect(
            self.world_position.x + self.offset.x - size // 2 + self.offset_x,
            self.world_position.y + self.offset.y - size // 2 + self.offset_y,
            size,
            size
        )

    def Draw_rock(self, screen: pygame.Surface, world_offset: pygame.Vector2):
        self.screen_x = (self.world_position.x - world_offset.x) + self.offset.x
        self.screen_y = (self.world_position.y - world_offset.y) + self.offset.y
        magnitude = RockData.magnitude

        self.r.seed(hash((self.world_position.x, self.world_position.y)))

        # cosmetic coord
        offset_x = self.r.choice([10, -10]) + self.r.randint(-10, 10)
        offset_y = self.r.choice([10, -10]) + self.r.randint(-10, 10)
        r2_magnitude = 70

        rect2 = pygame.Rect(
            (self.screen_x - r2_magnitude // 2) + self.offset_x + offset_x,
            (self.screen_y - r2_magnitude // 2) + self.offset_y + offset_y,
            r2_magnitude,
            r2_magnitude

        )
        rect = pygame.Rect(
            (self.screen_x - magnitude // 2) + self.offset_x,
            (self.screen_y - magnitude // 2) + self.offset_y,
            magnitude,
            magnitude
        )
        pygame.draw.rect(
            screen,
            Colour.grey,
            rect,
            border_radius=20
        )

        pygame.draw.rect(
            screen,
            Colour.light_grey,
            rect2,
            border_radius=10
        )


class Creature:
    def update(self, dt, world): raise NotImplementedError

    def draw(self, screen, offset):
        raise NotImplementedError


class FireFly(Creature):
    def __init__(self, world_position: pygame.Vector2):
        self.world_position = world_position
        self.seed = hash((int(self.world_position.x), int(self.world_position.y)))
        self.local_random = random.Random(self.seed)
        self.phase = self.local_random.uniform(0, math.tau)
        self.speed = self.local_random.uniform(0.6, 1.4)

        self.angle = self.local_random.uniform(0, math.tau)
        self.angluar_speed = self.local_random.uniform(0.3, 0.6)
        self.radius = self.local_random.uniform(5, 15)
        self.sensor = 50

        self.screen_x = 0
        self.screen_y = 0

    def linear_interpolation(self, a, b, t):
        return a + ((b - a) * t)

    def colour_interp(self, c1, c2, t):
        r = self.linear_interpolation(c1[0], c2[0], t)
        g = self.linear_interpolation(c1[1], c2[1], t)
        b = self.linear_interpolation(c1[2], c2[2], t)

        return (r, g, b)

    def draw_fire_fly(self, screen: pygame.Surface, player_reference: pygame.Vector2):
        # Conver world position to screen position.
        # polar coordinate
        # radius , angle
        self.angle += self.angluar_speed * 1 / 10

        if self.angle > math.tau:
            self.angle -= math.tau

        dx = math.cos(self.angle) * self.radius
        dy = math.sin(self.angle) * self.radius
        self.screen_x = self.world_position.x - player_reference.x + dx
        self.screen_y = self.world_position.y - player_reference.y + dy
        time = pygame.time.get_ticks() / 1000
        n = math.sin(time * self.speed + self.phase)
        glow = (n + 1) / 2
        radius = int(2 + glow * 2)
        colour = self.colour_interp((255, 255, 255), Colour.dark_grey, glow)

        pygame.draw.circle(
            screen, colour, (self.screen_x, self.screen_y), radius
        )
