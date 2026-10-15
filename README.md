# ACO Pathfinding Simulation

A desktop simulation that compares **Ant Colony Optimisation (ACO)** with **A\*** on a procedurally generated, unbounded world. Ants find a resource through stochastic movement and lay pheromone on the way back, so a trail emerges without any global map.

## Features

- Infinite terrain generated in chunks with Perlin noise (forest, grassland, ponds, trees and rocks)
- Terrain-weighted edge costs and a per-ant energy limit
- Pheromone deposit and evaporation, with live parameter sliders
- Emergent (greedy pheromone) path in cyan, A\* optimal path in magenta
- Live stats panel, including a **divergence** metric: how much longer the emergent path is than the optimal one

## Run

Requires Python 3.10+.

```
pip install -r requirements.txt
python main.py
```

On Linux you may also need tkinter: `sudo apt install python3-tk`

## Controls

- **Arrow keys**: move the camera
- **Control panel**: adjust evaporation, deposit strength, base pheromone, pheromone bias, ant count, max energy and steps per frame; reset pheromones or ants; toggle the cyan and A\* paths

## Project structure

```
main.py             entry point
aco/
  simulation.py     main loop, A* and path tracing
  agents.py         Ant, ResourceNode
  world.py          chunk generation, terrain cost, rendering
  scenery.py        trees, rocks, fireflies
  noise.py          Perlin noise
  control_panel.py  customtkinter UI
  colours.py        colour palette
```

## Documentation

Full analysis and design: [docs/analysis-and-design.pdf](docs/analysis-and-design.pdf)