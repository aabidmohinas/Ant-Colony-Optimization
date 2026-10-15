import math
import random
from itertools import product

import pygame

from .colours import Colour
from .scenery import Tree, Rock, FireFly


class Generation:
    def __init__(self, screen_dimension, perlin):
        self.screen_dimension: list = screen_dimension
        self.world_dimension: list = pygame.Vector2(0, 0)
        self.perlin = perlin
        self.grid_size = 60
        self.tile = 60
        self.chunk_size = 16
        self.chunk_size_pixel = self.tile * self.chunk_size
        self.world_chunk_coordinates: dict[tuple[int, int], dict] = {}
        self.loaded_chunk: set[tuple[int, int]] = set()
        self.current_chunk: tuple[int, int] = (0, 0)
        self.biome_scale: int = 800
        self.world_nodes: set[tuple[int, int]] = set()
        self.blocked_nodes: set[tuple[int, int]] = set()
        self.node_colours = {}
        self.grid_size = 60
        self.tile = 60
        self.node_step = 10

    def get_neighbours(self, node: tuple[int, int]) -> list[tuple[int, int]]:
        x, y = node
        step = self.grid_size // 2
        directions = [
            (step, 0), (-step, 0),
            (0, step), (0, -step),
        ]
        return [
            (x + dx, y + dy)
            for dx, dy in directions
            if (x + dx, y + dy) in self.world_nodes
            and (x + dx, y + dy) not in self.blocked_nodes
        ]

    def get_terrain_resistance(self, world_x, world_y) -> float:
        # sample noise and turn it into a movement multiplier
        # darker / rougher terrain should feel "heavier" to move across
        min_resistance = 0.2
        max_resistance = 1.0
        noise_val = self.perlin.octave(
            world_x / self.biome_scale,
            world_y / self.biome_scale,
            octaves=3,
            persistence=0.5,
            lacunarity=2.0
        )
        # perlin returns roughly [-1, 1]
        # convert that to [0, 1] so we can scale it cleanly
        normalised = (noise_val + 1) / 2
        resistance = min_resistance + normalised * (max_resistance - min_resistance)
        return resistance

    def get_edge_cost(self, node_i: tuple[int, int], node_j: tuple[int, int]) -> float:
        """C_ij = τ_ij * S_ij where τ_ij sampled at midpoint"""
        mx = (node_i[0] + node_j[0]) / 2
        my = (node_i[1] + node_j[1]) / 2
        tau = self.get_terrain_resistance(mx, my)
        s = math.dist(node_i, node_j)
        return tau * s

    def mark_blocked_nodes(self, chunk, chunk_pos):
        cx, cy = chunk_pos
        obstacles = []
        for tree in chunk["Trees"]:
            obstacles.append(tree.get_collision_rect())
        for rock in chunk["Rocks"]:
            obstacles.append(rock.get_collision_rect())
        if not obstacles:
            return
        # iterate over world_nodes directly instead of chunk["Nodes"]
        for (world_x, world_y) in self.world_nodes:
            for rect in obstacles:
                if rect.collidepoint(world_x, world_y):
                    self.blocked_nodes.add((world_x, world_y))
                    break

    def Chunk(self):
        # return chunk data which is loaded.
        for chunk_pos in self.loaded_chunk:
            if chunk_pos in self.world_chunk_coordinates:
                yield (self.world_chunk_coordinates[(chunk_pos)], chunk_pos)

    def Chunk_to_world(self, chunk_pos, grid_size, local_x, local_y):
        # convert chunk data to world position
        cx, cy = chunk_pos
        base_x = self.chunk_size_pixel * cx
        base_y = self.chunk_size_pixel * cy
        match (local_x, local_y):
            case (None, None):
                for gx, gy in product(
                    range(0, self.chunk_size_pixel, grid_size), repeat=2
                ):
                    yield (gx, gy, base_x + gx, base_y + gy)
            case (x, y) if x is not None and y is not None:
                yield (local_x, local_y, base_x + local_x, base_y + local_y)
            case _:
                raise ValueError(
                    "Either local (x,y) is both None or valid coordinates are provided")

    def Rendered_chunk(self, radius: int = 1) -> None:
        cx, cy = self.current_chunk
        self.loaded_chunk.clear()
        for dx, dy in product(
                range(-radius, radius + 1), repeat=2):
            self.loaded_chunk.add((cx + dx, cy + dy))

    def Create_chunks(self):

        cx = int(self.world_dimension.x // self.chunk_size_pixel)
        cy = int(self.world_dimension.y // self.chunk_size_pixel)
        for chunk_pos in self.loaded_chunk:
            if chunk_pos not in self.world_chunk_coordinates:
                self.world_chunk_coordinates[chunk_pos] = {

                    "Nodes": set(),
                    "Trees": set(),
                    "Rocks": set(),
                    "FireFly": set(),
                    "Spawn": (0, 0)
                }

    def Update_current_chunk(self) -> None:
        self.current_chunk = (
            int(self.world_dimension.x // self.chunk_size_pixel),
            int(self.world_dimension.y // self.chunk_size_pixel))

    def Generate_trees(self, chunk, chunk_pos, depth=4):

        for _, _, world_x, world_y in self.Chunk_to_world(chunk_pos, self.grid_size * depth, None, None):
            noise = self.perlin.perlin(world_x / self.biome_scale, world_y / self.biome_scale)
            biome, _ = self.Biome_type(noise)
            if biome == "forest":
                tree_scale = 1000
                tree_noise = self.perlin.octave(world_x / tree_scale, world_y / tree_scale, octaves=3, persistence=0.5, lacunarity=2.0)
                if (tree_noise + 1) / 2 > 0:
                    # ^ did this because perlin normally doesn't produce value > 0.5 -> so i normalised it to fit.
                    tree = Tree(pygame.Vector2(world_x, world_y))
                    chunk["Trees"].add(tree)

            if biome == "grassland":
                if random.randint(0, 100) < 60:
                    tree = Tree(pygame.Vector2(world_x, world_y))
                    chunk["Trees"].add(tree)

    def Generate_firefly(self, chunk, chunk_pos, depth=1):
        for _, _, world_x, world_y in self.Chunk_to_world(chunk_pos, self.grid_size * depth, None, None):
            fire_fly_scale = 500
            noise = self.perlin.octave(world_x / fire_fly_scale, world_y / fire_fly_scale, octaves=3, persistence=0.5, lacunarity=2.0)
            biome, _ = self.Biome_type(noise)

            if biome == "forest":
                if random.randint(0, 100) < 30:
                    fly = FireFly(pygame.Vector2(world_x, world_y))
                    chunk["FireFly"].add(fly)

    def Generate_rocks(self, chunk, chunk_pos, depth=6):

        for _, _, world_x, world_y in self.Chunk_to_world(chunk_pos, self.grid_size * depth, None, None):
            noise = self.perlin.perlin(world_x / self.biome_scale, world_y / self.biome_scale)
            biome, _ = self.Biome_type(noise)
            if biome == "forest":
                stone_scale = 800
                stone_noise = self.perlin.octave(world_x / stone_scale, world_y / stone_scale, octaves=3, persistence=0.5, lacunarity=2.0)
                if (stone_noise + 1) / 2 > 0 and (world_x, world_y) not in chunk["Trees"]:
                    rock = Rock(pygame.Vector2(world_x, world_y))
                    chunk["Rocks"].add(rock)

            if biome == "grassland":
                rock = Rock(pygame.Vector2(world_x, world_y))
                chunk["Rocks"].add(rock)

    def Chunk_data_manager(self) -> None:
        for chunk, chunk_pos in self.Chunk():
            if not chunk["Nodes"]:
                cx, cy = chunk_pos
                for local_x, local_y, world_x, world_y in self.Chunk_to_world(
                    chunk_pos, self.grid_size // 2, local_x=None, local_y=None
                ):
                    self.biome_scale = 3000
                    noise_val = self.perlin.octave(world_x / self.biome_scale, world_y / self.biome_scale, octaves=5, persistence=0.5, lacunarity=10.0)
                    water_noise = self.perlin.octave(world_x / 650, world_y / 650, octaves=2, persistence=1, lacunarity=2)
                    biome, colour = self.Biome_type(noise_val, water_noise_=water_noise)
                    self.node_colours[(chunk_pos, (local_x, local_y))] = colour
                    chunk["Nodes"].add((local_x, local_y))
                    self.world_nodes.add((world_x, world_y))
            if not chunk["Trees"]:
                self.Generate_trees(chunk, chunk_pos)
            if not chunk["FireFly"]:
                self.Generate_firefly(chunk, chunk_pos)
            if not chunk["Rocks"]:
                self.Generate_rocks(chunk, chunk_pos)
            self.mark_blocked_nodes(chunk, chunk_pos)

    def Biome_type(self, noise_value, water_noise_=0):
        """Biome logic. determines the colour gradient of the world"""

        if water_noise_ < -0.3: return ("void pond", Colour.black)
        elif -0.3 < water_noise_ < -0.275: return ("outer", Colour.middle_grey)
        elif noise_value < 0: return ("forest", Colour.dark_grey)
        # elif 0 < noise_value < 0.275: return ("outer" , Colour.middle_green )
        else: return ("grassland", Colour.light_grey)


class Render:
    def __init__(self, chunk_pixel_size, screen, grid_size):
        self.chunk_size_pixel = chunk_pixel_size
        self.screen = screen
        self.grid_size = grid_size

    def Draw_chunk(self, chunk_function, world_dimension: pygame.Vector2, node_colours: dict):
        """ Helper method to visualise chunks """
        for chunk, chunk_pos in chunk_function:
            cx, cy = chunk_pos
            screen_x = (cx * self.chunk_size_pixel) - world_dimension.x
            screen_y = (cy * self.chunk_size_pixel) - world_dimension.y
            rect = pygame.Rect(
                screen_x,
                screen_y,
                self.chunk_size_pixel,
                self.chunk_size_pixel
            )
            pygame.draw.rect(
                self.screen,
                Colour.yellow,
                rect,
                2
            )
            for nx, ny in chunk["Nodes"]:
                world_nx = (cx * self.chunk_size_pixel) + nx
                world_ny = (cy * self.chunk_size_pixel) + ny
                screen_x = world_nx - world_dimension.x
                screen_y = world_ny - world_dimension.y
                colour = node_colours[(chunk_pos, (nx, ny))]
                rect = pygame.Rect(
                    screen_x,
                    screen_y,
                    self.grid_size,
                    self.grid_size
                )
                pygame.draw.rect(
                    self.screen,
                    colour,
                    rect
                )
