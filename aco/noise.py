import math
import random


class Perlin_Noise:
    def __init__(self):
        self.gradients_node = {}
        self.seed_ = random.randint(0, 10000)

    def random_gradient(self, x, y):
        h = hash((x, y, self.seed_))
        angle = (h % 360) * math.pi / 180
        return (math.cos(angle), math.sin(angle))

    def fade(self, t):
        return (6 * (t ** 5)) - (15 * (t ** 4)) + (10 * (t ** 3))

    def dot_product(self, grid_x, grid_y, sample_x, sample_y):
        gradient_x, gradient_y = self.random_gradient(grid_x, grid_y)
        dx = sample_x - grid_x  # horizontal distance from the grid corner to one of the sample
        dy = sample_y - grid_y  # vertical distance from the grid corner to one of the sample
        return (gradient_x * dx) + (gradient_y * dy)

    def linear_interpolation(self, a1, a2, t):
        return a1 + ((a2 - a1) * t)

    def perlin(self, x, y):
        # say x = 7.8 , y = 6.5
        # I need to find the 4 grid corners of where x and y resides in
        x0 = math.floor(x)
        y0 = math.floor(y)
        x1 = x0 + 1
        y1 = y0 + 1

        # how far across sample x , y is from its respective axis
        dx = x - x0
        dy = y - y0

        # fade the values
        n = self.fade(dx)
        m = self.fade(dy)

        # get the dot products from the 4 corner
        dot_1 = self.dot_product(x0, y0, x, y)
        dot_2 = self.dot_product(x1, y0, x, y)
        dot_3 = self.dot_product(x0, y1, x, y)
        dot_4 = self.dot_product(x1, y1, x, y)

        # interpolate the top two dots , and the bottom two dots
        bottom_interp = self.linear_interpolation(dot_1, dot_2, n)
        top_interp = self.linear_interpolation(dot_3, dot_4, n)

        # blend the top interpolation and the bottom interpolation
        final_interp = self.linear_interpolation(bottom_interp, top_interp, m)

        return max(-1, min(1, final_interp))

    def octave(self, x, y, octaves=5, persistence=0.5, lacunarity=2.0):
        total = 0
        frequency = 1
        amplitude = 1
        max_value = 0

        for _ in range(octaves):
            total += self.perlin(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return total / max_value
