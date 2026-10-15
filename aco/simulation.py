import heapq
import math
import sys

import pygame

from .agents import Ant, ResourceNode
from .colours import Colour
from .control_panel import ControlPanel
from .noise import Perlin_Noise
from .scenery import Tree
from .world import Generation, Render


class Main:
    def __init__(self) -> None:
        pygame.init()
        # MMMM WIDHT AND HEIGHHTTTT
        self.screen_dimension: list = pygame.Vector2(800, 600)
        self.player_dimension: list = pygame.Vector2(40, 40)
        # main must be able to see most the world. tried to make it so that sub classes are not coupled
        # except for generation and render. render seems very coupled to the current codebase.
        # so perhaps i shouldve assigned render logic to main instead of creating a render class.
        # instantiating...
        self.perlin = Perlin_Noise()
        self.generation = Generation(self.screen_dimension, self.perlin)
        self.tree = Tree(self.generation.world_dimension)
        self.screen = pygame.display.set_mode((
            self.generation.screen_dimension.x,
            self.generation.screen_dimension.y
        ))
        self.render = Render(
            self.generation.chunk_size_pixel,
            self.screen,
            self.generation.grid_size
        )
        self.panel = ControlPanel()
        self.running: bool = True
        self.clock = pygame.time.Clock()
        self.keys = pygame.key.get_pressed()
        # force initial chunk generation so world_nodes is populated initially, so that the ants does do something in the first frame.
        self.generation.Update_current_chunk()
        self.generation.Rendered_chunk()
        self.generation.Create_chunks()
        self.generation.Chunk_data_manager()
        start_node = (0, 0)
        resource_node = (300, 300)
        self.resource = ResourceNode(resource_node)
        self.ants = [Ant(start_node) for _ in range(50)]
        self.cyan_reached_target = False
        self.pheromones = {}
        self.xi0 = 0.1  # base pheromone strength that exists everywhere
        # Just did ln(2) / 770, so that it has enough time to form a trail. for the beta var
        # there goes my time..
        self.beta = 0.0009  # evaporation rate. gotta be fancy with the names
        self.epsilon = 5.0  # how much an ant drops per edge
        self.alpha = 2.0  # pheromone bias... the exponent bit for probabilty in moy doc
        self.steps_per_frame = 10
        self.camera_point = pygame.Vector2(
            self.screen_dimension.x // 2,
            self.screen_dimension.y // 2
        )
        self.show_emergent_path = True
        # atmosphere is important.
        self.tint_surface = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.tint_surface.fill((12, 22, 34, 100))
        self.emergent_path_edges = []
        self.successful_returns = 0
        self.recent_path_lengths = []
        self.astar_path_edges = []
        self.astar_reached_target = False
        self.show_astar_path_flag = False
        self._measure_counter = 0
        self._measure_interval = 30

    def sync_panel(self):
        # this gets the value from how much the person using the sliders has changed the thing by.
        self.beta = self.panel.evaporation_rate.get()
        self.epsilon = self.panel.deposit_strength.get()
        self.xi0 = self.panel.base_pheromone.get()
        self.alpha = self.panel.pheromone_bias.get()
        self.steps_per_frame = int(self.panel.speed.get())
        # currently the code assumes the old value. so the count needs to be update to the target value , i.e. current is the old value
        target = int(self.panel.ant_count.get())
        current = len(self.ants)
        energy = self.panel.max_energy.get()
        start = self.ants[0].get_start_position if self.ants else (0, 0)
        if target > current:
            # increment if the count is greater
            for _ in range(target - current):
                self.ants.append(Ant(start, max_energy=energy))
        # otherwise decrement by slicing...
        elif target < current:
            self.ants = self.ants[:target]
        for ant in self.ants:
            ant.max_energy = energy
        if self.panel.should_reset_pheromones():
            self.pheromones.clear()  # namely, if the user presses the clear button, it empties the pheromone dict.
            self.successful_returns = 0  # as the name describes..
            self.recent_path_lengths = []  # keeps the current 50 path. if reset then empty it.
        if self.panel.should_reset_ants():
            for ant in self.ants:
                ant.reset()  # similar logic as above..
        self.show_emergent_path = self.panel.show_cyan_path.get()
        self.show_astar_path_flag = self.panel.show_astar_path.get()
        returning = 0
        exhausted = 0
        active = 0
        # simple boolean checks to count the appropriate number and display it on the panel.
        for ant in self.ants:
            if ant.returning:
                returning += 1
            elif ant.exhausted:
                exhausted += 1
            else:
                active += 1
        if self.pheromones:
            max_val = max(self.pheromones.values())
        else:
            max_val = 0
        if self.recent_path_lengths:
            avg_path = sum(self.recent_path_lengths) / len(self.recent_path_lengths)  # well.. average
        else:
            avg_path = 0.0
        if (self.cyan_reached_target and self.astar_reached_target and len(self.astar_path_edges) > 0):
            l_o = sum(self.generation.get_edge_cost(u, v) for u, v in self.astar_path_edges)
            l_e = sum(self.generation.get_edge_cost(u, v) for u, v in self.emergent_path_edges)
            if l_o > 0:
                divergence = f"{(l_e - l_o) / l_o:.4f}"
            else:
                divergence = "N/A (infinite optimal path)"
        else:
            divergence = "N/A"
        # pass the required parameters to the controlpanel instance for it to use
        # did it this way so that control panel wont touch the other classes except main.
        self.panel.receive_stats(
            num_edges=len(self.pheromones),
            max_xi=max_val,
            returning=returning,
            exhausted=exhausted,
            active=active,
            evaporation=self.beta,
            total_ants=len(self.ants),
            successful_returns=self.successful_returns,
            avg_path_length=avg_path,
            cyan_length=len(self.emergent_path_edges),
            cyan_reached=self.cyan_reached_target,
            astar_length=len(self.astar_path_edges),
            astar_reached=self.astar_reached_target,
            divergence=divergence
        )
        self.panel.tick()

    def update_pheromones(self):
        # gradually fade all pheromones each step
        # if decay feels too strong/weak, tweak evaporation_rate
        to_remove = []
        for edge in self.pheromones:
            self.pheromones[edge] *= (1 - self.beta)
            # delete tiny trails so dictionary doesn't grow forever
            # 1e^-6 is just a very small number. tried to reduce redundant memory usage...
            if self.pheromones[edge] < 1e-6:
                to_remove.append(edge)
        for edge in to_remove:
            del self.pheromones[edge]

    def draw_camera_point(self):
        # DRAWW THE POINT THAT YOU CAN BARELY SEE IN THE MIDDLE OF THE SCREEN.
        pygame.draw.circle(
            self.screen,
            Colour.black,
            self.camera_point,
            3
        )

    def Event(self) -> None:
        # Hm.. this sepecifically reduces the frames but.. it is dead code since it can be controlled by the slider
        # i suppose i can leave it here for now..
        for events in pygame.event.get():
            if events.type == pygame.QUIT:
                self.running = False
                sys.exit()
            if events.type == pygame.KEYDOWN:
                if events.key == pygame.K_EQUALS:
                    self.steps_per_frame = min(100, self.steps_per_frame + 5)
                if events.key == pygame.K_MINUS:
                    self.steps_per_frame = max(1, self.steps_per_frame - 5)

    def measure_emergent_path(self):
        start = (0, 0)  # ants always spawns here
        target = self.resource.node_position
        # set up the initial conditions to trace through iteratively.
        current = start
        visited = set()
        self.emergent_path_edges = []  # reset the edges so it recalculates every 30 frame, so that if it changes it appears on the screen.
        self.cyan_reached_target = False  # consider it to not have reached at the start..
        cumulative_cost = 0.0
        # limit it for 1000 iterations so that it wont be stuck in an infinite loop.
        for _ in range(1000):
            if current == target:
                self.cyan_reached_target = True  # allows it to be shown on the panel...
                return
            # keep track of the visited nodes, so that it wont go back and forth..
            visited.add(current)
            neighbours = self.generation.get_neighbours(current)  # well.. neighbours..
            best_node = None
            best_value = 0.0
            for n in neighbours:
                if n in visited:
                    # even tho the graph allows cycles, i prevent this so that it wont well.. get stuck in a loop.
                    continue
                # getting the key value pair for the dictionary, and need to order it to match the way it is stored.
                edge = (min(current, n), max(current, n))
                strength = self.pheromones.get(edge, 0.0)  # well.. get the strength at that edge
                if strength > best_value:
                    # greedily choose the strongest pheromone trail..
                    best_value = strength
                    best_node = n
            if best_node is None:
                # path ended..
                return
            # get the terrain weighted cost and increment cumulative cost..
            step_cost = self.generation.get_edge_cost(current, best_node)
            cumulative_cost += step_cost
            if cumulative_cost > self.panel.max_energy.get():
                # the ant will not have any stamina..
                return
            self.emergent_path_edges.append((current, best_node))
            current = best_node  # move onto the next node and repeat...

    def compute_astar_path(self):
        start = (0, 0)  # ants always spawns here
        goal = self.resource.node_position
        self.astar_path_edges = []
        self.astar_reached_target = False
        # priority queue entries: (f_score, counter, node)
        # counter breaks ties so tuples with equal f don't compare nodes
        open_set = []
        counter = 0
        heapq.heappush(open_set, (0.0, counter, start))
        g_score = {start: 0.0}
        came_from = {}
        closed_set = set()
        while open_set:
            f_current, _, current = heapq.heappop(open_set)
            if current == goal:
                # reconstruct path
                self.astar_reached_target = True
                path = []
                node = goal
                while node in came_from:
                    prev = came_from[node]
                    path.append((prev, node))
                    node = prev
                path.reverse()  # return the reverse since it goes from parent -> child
                self.astar_path_edges = path
                return
            if current in closed_set:
                # ignore this node if its already visited
                continue
            closed_set.add(current)
            for neighbour in self.generation.get_neighbours(current):
                if neighbour in closed_set:
                    continue
                edge_cost = self.generation.get_edge_cost(current, neighbour)
                tentative_g = g_score[current] + edge_cost
                if tentative_g > self.panel.max_energy.get():
                    # unreachable within energy budget
                    continue
                if tentative_g < g_score.get(neighbour, float('inf')):
                    came_from[neighbour] = current
                    g_score[neighbour] = tentative_g
                    # heuristic: euclidean distance scaled by minimum possible resistance
                    h = math.dist(neighbour, goal) * 0.2
                    f = tentative_g + h
                    counter += 1
                    heapq.heappush(open_set, (f, counter, neighbour))
        # no path found
        self.astar_path_edges = []
        self.astar_reached_target = False

    def draw_emergent_path(self):
        # well skip drawing of the toggle is off.
        if not self.show_emergent_path:
            return
        if not self.emergent_path_edges:
            return
        # otherwise or equilivent to an else statement..
        for n1, n2 in self.emergent_path_edges:
            # find the difference in world and screen and draw the manhattan distance..
            p1 = (
                int(n1[0] - self.generation.world_dimension.x),
                int(n1[1] - self.generation.world_dimension.y)
            )
            p2 = (
                int(n2[0] - self.generation.world_dimension.x),
                int(n2[1] - self.generation.world_dimension.y)
            )
            pygame.draw.line(self.screen, (0, 255, 255), p1, p2, 3)

    def draw_astar_path(self):
        # well skip drawing if the toggle is off.
        if not self.show_astar_path_flag:
            return
        if not self.astar_path_edges:
            return
        # otherwise draw the A* optimal path in magenta
        for n1, n2 in self.astar_path_edges:
            # find the difference in world and screen and draw the manhattan distance..
            p1 = (
                int(n1[0] - self.generation.world_dimension.x),
                int(n1[1] - self.generation.world_dimension.y)
            )
            p2 = (
                int(n2[0] - self.generation.world_dimension.x),
                int(n2[1] - self.generation.world_dimension.y)
            )
            pygame.draw.line(self.screen, (255, 0, 255), p1, p2, 3)

    def draw_pheromones(self):
        # similar logic to the draw emergent method
        if not self.pheromones:
            return
        max_xi = max(self.pheromones.values())
        if max_xi < 1e-6:
            return
        for (n1, n2), xi in self.pheromones.items():
            ratio = min(1.0, xi / max_xi)
            intensity = int(255 * ratio)
            colour = (intensity, intensity // 3, 0)
            p1 = (
                int(n1[0] - self.generation.world_dimension.x),
                int(n1[1] - self.generation.world_dimension.y)
            )
            p2 = (
                int(n2[0] - self.generation.world_dimension.x),
                int(n2[1] - self.generation.world_dimension.y)
            )
            width = max(1, int(3 * ratio))
            pygame.draw.line(self.screen, colour, p1, p2, width)

    def Update(self) -> None:
        self.keys = pygame.key.get_pressed()
        dt = self.clock.tick(60) / 1000
        observer_speed = 400
        dx = dy = 0
        # move the camera
        if self.keys[pygame.K_UP]:
            dy -= observer_speed * dt
        if self.keys[pygame.K_DOWN]:
            dy += observer_speed * dt
        if self.keys[pygame.K_LEFT]:
            dx -= observer_speed * dt
        if self.keys[pygame.K_RIGHT]:
            dx += observer_speed * dt
        self.generation.world_dimension.x += dx
        self.generation.world_dimension.y += dy
        self.screen.fill(Colour.background_grey)
        for _ in range(self.steps_per_frame):
            for ant in self.ants:
                if ant.exhausted:
                    # they die.
                    # you can see the corpse in the screen.
                    continue
                if ant.returning:
                    ant.return_step(self.pheromones, self.epsilon, self.generation)  # if they found food, then they will drop pheromones along the path,
                else:
                    # otherwise just keep moving till it finds something.. or die.
                    ant.move(self.generation, self.pheromones, self.xi0, self.alpha)
                    if ant.node_position == self.resource.node_position:
                        ant.reached_resource = True
                        ant.begin_return()
            self.update_pheromones()
        for ant in self.ants:
            if ant.has_deposited or ant.exhausted:
                if ant.has_deposited:
                    # data for the panel..
                    self.successful_returns += 1
                    self.recent_path_lengths.append(ant.return_cost)
                    if len(self.recent_path_lengths) > 50:
                        # limit memory usage.
                        self.recent_path_lengths.pop(0)
                ant.reset()
        # measued every 30 frames and drawn on the screen.
        # measued every 30 frames and drawn on the screen.
        if self.show_emergent_path:
            self._measure_counter += 1
            if self._measure_counter >= self._measure_interval:
                self._measure_counter = 0
                self.measure_emergent_path()
        else:
            self.emergent_path_edges = []
        # A* computed on the same interval so it doesn't bog down every frame
        if self.show_astar_path_flag:
            # only recompute when the emergent path also refreshes (or first time)
            if not self.astar_path_edges or self._measure_counter == 0:
                self.compute_astar_path()
        else:
            self.astar_path_edges = []

    def Run(self) -> None:
        # RUN INTIALISE AND RUN THE SIMULATION.
        while self.running:
            self.Event()
            self.Update()
            self.generation.Update_current_chunk()
            self.generation.Rendered_chunk()
            self.generation.Create_chunks()
            self.generation.Chunk_data_manager()
            self.render.Draw_chunk(
                self.generation.Chunk(),
                self.generation.world_dimension,
                self.generation.node_colours
            )
            for chunk, _ in self.generation.Chunk():
                for rock in chunk["Rocks"]:
                    rock.Draw_rock(self.screen, self.generation.world_dimension)
                for tree in chunk["Trees"]:
                    tree.Draw_tree(self.screen, self.generation.world_dimension)
                for fly in chunk["FireFly"]:
                    fly.draw_fire_fly(self.screen, self.generation.world_dimension)
            self.draw_pheromones()
            self.draw_emergent_path()
            self.draw_astar_path()

            self.resource.draw(self.screen, self.generation.world_dimension)
            for ant in self.ants:
                ant.draw(self.screen, self.generation.world_dimension)
            self.screen.blit(self.tint_surface, (0, 0))
            self.draw_camera_point()
            self.sync_panel()
            pygame.display.flip()
