import math

import customtkinter as ctk


class ControlPanel:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.root = ctk.CTk()
        self.root.title("ACO Controls")
        self.root.geometry("400x750")
        self.reset_pheromones_pressed = False
        self.reset_ants_pressed = False
        self.measure_pressed = False
        # set the default value for the parameters that seem appropriate.
        self.evaporation_rate = ctk.DoubleVar(value=0.0009)
        self.deposit_strength = ctk.DoubleVar(value=5.0)
        self.base_pheromone = ctk.DoubleVar(value=0.1)
        self.pheromone_bias = ctk.DoubleVar(value=2.0)
        self.ant_count = ctk.DoubleVar(value=50)
        self.max_energy = ctk.DoubleVar(value=5000)
        self.speed = ctk.DoubleVar(value=10)

        self.show_cyan_path = ctk.BooleanVar(value=True)
        self.show_astar_path = ctk.BooleanVar(value=False)
        self.build_ui()

    # update method to check if the user checked the button. bool var changes to an appropriate state.
    def press_reset_pheromones(self): self.reset_pheromones_pressed = True

    def press_reset_ants(self): self.reset_ants_pressed = True

    def press_measure(self): self.measure_pressed = True

    # conditional check to set new updated values.
    def should_reset_pheromones(self):
        if self.reset_pheromones_pressed:
            self.reset_pheromones_pressed = False
            return True
        return False

    def should_reset_ants(self):
        if self.reset_ants_pressed:
            self.reset_ants_pressed = False
            return True
        return False

    def should_measure(self):
        if self.measure_pressed:
            self.measure_pressed = False
            return True
        return False

    # creating a toggle for the pheromone greedy path to show [tick] or [hide.]
    def toggle_cyan_path(self):
        current = self.show_cyan_path.get()
        self.show_cyan_path.set(not current)
        state = "ON" if not current else "OFF"
        self.cyan_toggle.configure(text=f"Cyan Path: {state}")

    # recieves the stats and formats it neatly
    def receive_stats(self, num_edges, max_xi, returning, exhausted, active,
                      evaporation, total_ants, successful_returns, avg_path_length,
                      cyan_length, cyan_reached, astar_length, astar_reached, divergence):
        # this calculates how long it takes for the pheromone strength to reach half its value
        # i used the same formula as in radiaoctivity.
        # where t_1/2 = ln(2) / lambda, where here its the evaporation rate.
        # thats why i set the intial beta value to be 0.0009, which is called the evaporation rate in this code
        # since ln(2) / 0.0009 is approximately 770 steps, so that the ants have enough time to form a proper trail
        # do note that infinity value can also be 0.
        # nvm u cant set to inf, it breaks it cuz of overflow and besides its meant to be a small number rather than inf.
        half_life = math.log(2) / evaporation if evaporation > 0 else 0
        text = (
            f"--- Colony ---\n"
            f"Total Ants: {total_ants}\n"
            f"Active: {active}\n"
            f"Returning: {returning}\n"
            f"Exhausted: {exhausted}\n"
            f"Successful Returns: {successful_returns}\n"
            f"\n"
            f"--- Pheromone ---\n"
            f"Active Edges: {num_edges}\n"
            f"Strongest Trail: {max_xi:.3f}\n"
            f"Half-Life: {int(half_life)} steps\n"
            f"\n"
            f"--- Greedy Path ---\n"
            f"Length: {cyan_length} edges\n"
            f"Reached Target: {'Yes' if cyan_reached else 'No'}\n"
            f"\n"
            f"--- A* Path ---\n"
            f"Length: {astar_length} edges\n"
            f"Reached Target: {'Yes' if astar_reached else 'No'}\n"
            f"\n"
            f"--- Performance ---\n"
            f"Avg Path Length: {avg_path_length:.1f}\n"
            f"\n"
            f"--- Divergence ---\n"
            f"Divergence: {divergence}\n"
        )
        self.stats_label.configure(text=text)

    def tick(self):
        # PRESSSS
        try: self.root.update()
        except: pass

    def make_slider(self, parent, text, variable, min_val, max_val):
        # set a helper method to create future sliders.
        label = ctk.CTkLabel(parent, text=text)
        label.pack(anchor="w")
        slider = ctk.CTkSlider(parent, from_=min_val, to=max_val, variable=variable)
        slider.pack(fill="x", pady=5)

    def build_ui(self):
        # creates the base ui with sliders and buttons for the parameters and stats.
        frame = ctk.CTkScrollableFrame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        title = ctk.CTkLabel(frame, text="Simulation Controls")
        title.pack(pady=10)
        # the range from intial to the maximum rate, must be < 1 for some constants since .. well.. evaporation...
        self.make_slider(frame, "Evaporation", self.evaporation_rate, 0.0001, 0.05)  # again.. evaporation cannot be 0, but still set a max so that it isnt instant.
        self.make_slider(frame, "Deposit Strength", self.deposit_strength, 0.1, 100.0)
        self.make_slider(frame, "Base Pheromone", self.base_pheromone, 0.001, 1.0)
        self.make_slider(frame, "Pheromone Bias", self.pheromone_bias, 0.1, 5.0)
        self.make_slider(frame, "Ant Count", self.ant_count, 1, 200)
        self.make_slider(frame, "Max Energy", self.max_energy, 500, 50000)  # hm.. seems kinda pointless because.. they cant change the where the resource spawns anyway.
        self.make_slider(frame, "Steps per Frame", self.speed, 1, 100)
        ctk.CTkButton(frame, text="Reset Pheromones",
                      command=self.press_reset_pheromones).pack(fill="x", pady=3)
        ctk.CTkButton(frame, text="Reset Ants",
                      command=self.press_reset_ants).pack(fill="x", pady=3)

        ctk.CTkCheckBox(frame, text="| Calculate Pheromone Greedy Path |", variable=self.show_cyan_path).pack(fill="x", pady=3)
        ctk.CTkCheckBox(frame, text="| Calculate A* Path |", variable=self.show_astar_path).pack(fill="x", pady=3)
        self.stats_label = ctk.CTkLabel(frame, text="Waiting...", justify="left")
        self.stats_label.pack(pady=15)
