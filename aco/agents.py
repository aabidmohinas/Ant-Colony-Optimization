import random

import pygame

from .colours import Colour


class Entity:
    def __init__(self, node_position: tuple[int, int]):
        self._node_position = node_position  # ← make private here too

    @property
    def node_position(self):
        return self._node_position

    def get_neighbours(self, world):
        return world.get_neighbours(self._node_position)


class ResourceNode(Entity):
    def __init__(self, node_position):
        super().__init__(node_position)

    def draw(self, screen, world_offset):
        screen_x = self._node_position[0] - world_offset.x
        screen_y = self._node_position[1] - world_offset.y
        pygame.draw.circle(
            screen,
            Colour.yellow,
            (int(screen_x), int(screen_y)),
            8
        )


class Ant(Entity):
    def __init__(self, node_position, max_energy=5000.0):
        super().__init__(node_position)
        self._start_position = node_position
        self._max_energy = max_energy
        self._energy = max_energy
        self._path = []
        self._reached_resource = False
        self._has_deposited = False
        self._exhausted = False
        self._returning = False
        self._return_path = []
        self._return_index = 0
        self._resource_step = None
        self._return_cost = 0.0

    # allows data be accessed and compared in other classes, while preserving ants internal integrity.
    @property
    def returning(self): return self._returning

    @property
    def exhausted(self): return self._exhausted

    @property
    def has_deposited(self): return self._has_deposited

    @property
    def return_path(self): return self._return_path

    @property
    def energy(self): return self._energy

    @property
    def return_cost(self): return self._return_cost

    @property
    def get_start_position(self): return self._start_position

    @property
    def reached_resource(self): return self._reached_resource

    @reached_resource.setter
    def reached_resource(self, value: bool): self._reached_resource = value

    @property
    def max_energy(self): return self._max_energy

    @max_energy.setter
    def max_energy(self, max_energy): self._max_energy = max_energy

    def move(self, world, pheromones, base_pheromone, pheromone_bias=2.0):
        if self._exhausted:
            # ant dies
            return
        neighbours = self.get_neighbours(world)
        if not neighbours:
            # in case its sorounded by obstacles, therefore prevents further execution of the code.
            return
        options = []
        weights = []
        for n in neighbours:
            # getting the cost from the current node to the neighbour node.
            cost = world.get_edge_cost(self._node_position, n)
            if self._energy - cost <= 0:
                # ant dies if this is executed, so i skip the trivial execution of the code
                continue

            # because, again in the dictionary the key is ordered in such a way...
            edge = (min(self._node_position, n), max(self._node_position, n))
            current_pheromone = pheromones.get(edge, 0.0)  # get the pheromone here, or 0 if it doesnt exist- ignores baseline pheromone.
            attraction = current_pheromone + base_pheromone  # then here i add the baseline pheromone...
            weight = attraction ** pheromone_bias  # again the operation of P_ij being proportional to the sum(pheromone , baseline)^ constant
            # the valid paths, incase its greater than 1
            options.append((n, cost))
            weights.append(weight)
        if not options:
            # if not path exist, kill the ant by exhaustion
            self._exhausted = True
            return
        total_weight = sum(weights)
        # normalise the weights to get probabilities
        probs = [w / total_weight for w in weights]
        # if theres more than one option then choose randomly.
        chosen_index = random.choices(range(len(options)), probs)[0]
        # get the chosen option's node and cost
        next_node, cost = options[chosen_index]
        self._energy -= cost
        self._path.append((self._node_position, next_node))  # keep an internal record of the path so that it can backtrack.
        self._node_position = next_node

    def begin_return(self):
        # this occurs when the ant does find a resource point, so it backtracks through its internal record of the path it came from
        self._returning = True
        self._return_cost = 0.0
        seen = {}
        clean_path = []
        # access the ants internal path rec.
        for i, (a, b) in enumerate(self._path):
            # this bit effectively attempts to remove cycles in the path
            # dont by saving a clean path and looping through that
            # i.e. if a graph exists such as A->B->C->D->B->E then it wouldve looped back to B , so remove the mid section and make it A->B->E.
            if a not in seen:
                seen[a] = len(clean_path)
                clean_path.append((a, b))
            else:
                clean_path = clean_path[:seen[a]]
                new_seen = {}
                for j, (x, y) in enumerate(clean_path):
                    new_seen[x] = j
                seen = new_seen
                clean_path.append((a, b))
                seen[a] = len(clean_path) - 1
        # not including current pos, because the ant is already there, so it doesnt need to backtrack to it.
        self._return_path = [(b, a) for (a, b) in reversed(clean_path)]
        self._return_index = 0

    def return_step(self, pheromones, deposit_strength, world):
        if self._return_index >= len(self._return_path):
            self._has_deposited = True
            # has finished the path so nothing happens, ant starts journey again..
            return
        # integer increments and allows a trace through the clean return path.
        edge = self._return_path[self._return_index]
        # i did intially store paths as sorted in tuples, i.e (A,B), it was to prevent duplicates.
        path_length = max(1, len(self._return_path))
        normalised_edge = (min(edge[0], edge[1]), max(edge[0], edge[1]))
        path_length = max(1, len(self._return_path))  # in case of zerodivision error.
        deposit_amount = deposit_strength / path_length  # shorter path is rewarded more.

        # collect the cumulative pheromone in this edge.
        pheromones[normalised_edge] = (
            pheromones.get(normalised_edge, 0.0) + deposit_amount
        )
        self._return_cost += world.get_edge_cost(edge[0], edge[1])
        self._node_position = edge[1]
        self._return_index += 1

    def reset(self):
        self._node_position = self._start_position
        self._energy = self._max_energy
        self._path = []
        self._reached_resource = False
        self._has_deposited = False
        self._exhausted = False
        self._returning = False
        self._return_path = []
        self._return_index = 0
        self._resource_step = None
        self._return_cost = 0.0

    def draw(self, screen, world_offset):
        screen_x = self._node_position[0] - world_offset.x
        screen_y = self._node_position[1] - world_offset.y
        if self._returning:
            colour = Colour.yellow
        else:
            colour = Colour.white
        pygame.draw.circle(
            screen,
            colour,
            (int(screen_x), int(screen_y)),
            5
        )
