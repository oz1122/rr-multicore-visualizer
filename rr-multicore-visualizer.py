import tkinter as tk
from tkinter import ttk, messagebox, Scale
import collections
import time
import random
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
CORE_AREA_Y_START = 100
CORE_AREA_HEIGHT = 150
QUEUE_AREA_Y_START = CORE_AREA_Y_START + CORE_AREA_HEIGHT + 50
QUEUE_AREA_HEIGHT = 150
PROCESS_RADIUS = 15
ANIMATION_STEP_DELAY_MS = 1000 
ANIMATION_MOVE_STEPS = 30

class Process:
    """Represents a process with its properties and visual representation."""
    def __init__(self, p_id, arrival_time, burst_time, canvas, color):
        self.id = p_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_burst_time = burst_time
        self.start_time = -1
        self.completion_time = -1
        self.waiting_time = 0
        self.turnaround_time = 0
        self.state = "New" 
        self.current_core = None
        self.time_on_core_current_quantum = 0
        self.canvas = canvas
        self.color = color
        self.visual_id = None
        self.text_id = None 
        self.target_x = None
        self.target_y = None
        self.current_x = None
        self.current_y = None

    def create_visual(self, x, y):
        """Creates the visual representation on the canvas."""
        self.current_x = x
        self.current_y = y
        self.visual_id = self.canvas.create_oval(
            x - PROCESS_RADIUS, y - PROCESS_RADIUS,
            x + PROCESS_RADIUS, y + PROCESS_RADIUS,
            fill=self.color, outline="black"
        )
        self.text_id = self.canvas.create_text(
            x, y, text=f"P{self.id}", fill="white"
        )
        self.canvas.tag_raise(self.text_id, self.visual_id) 

    def move_visual(self, dx, dy):
        """Moves the visual representation by dx, dy."""
        if self.visual_id:
            self.canvas.move(self.visual_id, dx, dy)
            self.canvas.move(self.text_id, dx, dy)
            self.current_x += dx
            self.current_y += dy

    def set_position(self, x, y):
        """Instantly sets the visual representation's position."""
        if self.visual_id:
            dx = x - self.current_x
            dy = y - self.current_y
            self.move_visual(dx, dy) 

    def destroy_visual(self):
        """Removes the visual representation from the canvas."""
        if self.visual_id:
            self.canvas.delete(self.visual_id)
            self.canvas.delete(self.text_id)
            self.visual_id = None
            self.text_id = None

    def update_tooltip(self, text):
         """ Placeholder for potentially showing process details on hover """

         pass

    def __repr__(self):
        return f"P{self.id} (AT:{self.arrival_time}, BT:{self.burst_time})"

class RRSchedulerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Multicore Round Robin Scheduling Simulator")
        self.master.geometry("1000x800") 

        self.processes = []
        self.ready_queue = collections.deque()
        self.terminated_processes = []
        self.cores = [] 
        self.gantt_data = []

        self.current_time = 0
        self.time_quantum = 1
        self.num_cores = 2
        self.simulation_running = False
        self.simulation_paused = False
        self.animation_speed_factor = 1.0 # 1.0
        self.process_counter = 0
        self.colors = ["red", "blue", "green", "orange", "purple", "brown", "pink", "cyan", "magenta", "yellow", "lime", "teal"]
        random.shuffle(self.colors)
        self.color_index = 0

        self._setup_gui()

    def _get_next_color(self):
        """Cycles through the color list."""
        color = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1
        return color

    def _setup_gui(self):
        """Creates and arranges the GUI elements."""
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        ttk.Label(control_frame, text="Arrival Time:").grid(row=0, column=0, sticky="w", pady=2)
        self.arrival_time_entry = ttk.Entry(control_frame, width=5)
        self.arrival_time_entry.grid(row=0, column=1, sticky="w", pady=2)
        self.arrival_time_entry.insert(0, "0")

        ttk.Label(control_frame, text="Burst Time:").grid(row=1, column=0, sticky="w", pady=2)
        self.burst_time_entry = ttk.Entry(control_frame, width=5)
        self.burst_time_entry.grid(row=1, column=1, sticky="w", pady=2)
        self.burst_time_entry.insert(0, "5")

        self.add_process_button = ttk.Button(control_frame, text="Tambah Process", command=self.add_process)
        self.add_process_button.grid(row=2, column=0, columnspan=2, pady=5)

        ttk.Label(control_frame, text="List Proses:").grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.process_listbox = tk.Listbox(control_frame, height=8, width=30)
        self.process_listbox.grid(row=4, column=0, columnspan=2, pady=2, sticky="ew")

        ttk.Label(control_frame, text="Quantum Time:").grid(row=5, column=0, sticky="w", pady=2)
        self.time_quantum_spinbox = tk.Spinbox(control_frame, from_=1, to=10, width=5, wrap=True)
        self.time_quantum_spinbox.grid(row=5, column=1, sticky="w", pady=2)
        self.time_quantum_spinbox.delete(0, tk.END)
        self.time_quantum_spinbox.insert(0, "2") # Default

        ttk.Label(control_frame, text="Number of Cores:").grid(row=6, column=0, sticky="w", pady=2)
        self.num_cores_spinbox = tk.Spinbox(control_frame, from_=1, to=8, width=5, wrap=True, command=self._update_core_display_on_change)
        self.num_cores_spinbox.grid(row=6, column=1, sticky="w", pady=2)
        self.num_cores_spinbox.delete(0, tk.END)
        self.num_cores_spinbox.insert(0, "2") # Default

        self.start_button = ttk.Button(control_frame, text="Mulai Simulasi", command=self.start_simulation)
        self.start_button.grid(row=7, column=0, columnspan=2, pady=(15, 5))

        self.pause_button = ttk.Button(control_frame, text="Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.grid(row=8, column=0, columnspan=2, pady=5)

        self.reset_button = ttk.Button(control_frame, text="Reset", command=self.reset_simulation)
        self.reset_button.grid(row=9, column=0, columnspan=2, pady=5)

        ttk.Label(control_frame, text="Animation Speed:").grid(row=10, column=0, columnspan=2, sticky="w", pady=(10, 0))
        self.speed_scale = Scale(control_frame, from_=0.2, to=3.0, resolution=0.1, orient=tk.HORIZONTAL, label="Faster <-> Slower", command=self.update_speed)
        self.speed_scale.set(1.0) # Default
        self.speed_scale.grid(row=11, column=0, columnspan=2, sticky="ew")

        self.time_label = ttk.Label(control_frame, text="Time: 0", font=("Arial", 12))
        self.time_label.grid(row=12, column=0, columnspan=2, pady=(15, 5))

        vis_frame = ttk.Frame(main_frame, padding="10")
        vis_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(vis_frame, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg="white", scrollregion=(0,0,CANVAS_WIDTH, CANVAS_HEIGHT + 200))
        hbar = ttk.Scrollbar(vis_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        vbar = ttk.Scrollbar(vis_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)


        self._draw_simulation_areas()

        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.results_label = ttk.Label(results_frame, text="Waiting for simulation end...")
        self.results_label.pack(pady=5)

        self._update_core_display_on_change()


    def _draw_simulation_areas(self):
        """Draws the static parts of the simulation area like core boxes and queue area."""
        self.canvas.delete("areas") # Clear

        self.canvas.create_text(10, CORE_AREA_Y_START - 15, text="CPU Cores:", anchor="w", font=("Arial", 12, "bold"), tags="areas")
        self.canvas.create_rectangle(5, CORE_AREA_Y_START, CANVAS_WIDTH - 5, CORE_AREA_Y_START + CORE_AREA_HEIGHT, outline="gray", dash=(2, 2), tags="areas")

        self.canvas.create_text(10, QUEUE_AREA_Y_START - 15, text="Ready Queue:", anchor="w", font=("Arial", 12, "bold"), tags="areas")
        self.canvas.create_rectangle(5, QUEUE_AREA_Y_START, CANVAS_WIDTH - 5, QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT, outline="gray", dash=(2, 2), tags="areas")

        self.gantt_y_start = QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT + 50
        self.canvas.create_text(10, self.gantt_y_start - 15, text="Gantt Chart:", anchor="w", font=("Arial", 12, "bold"), tags="areas")

        self._update_core_display()


    def _update_core_display_on_change(self, event=None):
        """Handles changes in the number of cores spinbox."""
        if self.simulation_running:
             messagebox.showwarning("Warning", "Cannot change core count during simulation. Reset first.")
             self.num_cores_spinbox.delete(0, tk.END)
             self.num_cores_spinbox.insert(0, str(self.num_cores)) # Revert
             return
        try:
            self.num_cores = int(self.num_cores_spinbox.get())
            if not 1 <= self.num_cores <= 8:
                raise ValueError("Core count must be between 1 and 8.")
            self._update_core_display()
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid number of cores: {e}")
            self.num_cores_spinbox.delete(0, tk.END)
            self.num_cores_spinbox.insert(0, str(self.num_cores)) # Revert


    def _update_core_display(self):
         """Draws or redraws the core representations."""
         self.canvas.delete("core_visual") # Clear

         core_box_width = (CANVAS_WIDTH - 20) / self.num_cores
         core_box_height = CORE_AREA_HEIGHT * 0.6
         y_pos = CORE_AREA_Y_START + (CORE_AREA_HEIGHT - core_box_height) / 2

         self.cores = [] # Reset

         for i in range(self.num_cores):
             x_start = 10 + i * core_box_width
             x_end = x_start + core_box_width - 10 # Small
             center_x = (x_start + x_end) / 2
             center_y = y_pos + core_box_height / 2

             core_id = self.canvas.create_rectangle(
                 x_start, y_pos, x_end, y_pos + core_box_height,
                 outline="blue", fill="lightblue", tags=("core_visual", f"core_{i}")
             )
             self.canvas.create_text(
                 center_x, y_pos - 10, text=f"Core {i}", anchor="s", tags=("core_visual", f"core_text_{i}")
             )
             self.cores.append({
                 'id': i,
                 'state': 'Idle',
                 'process': None,
                 'visual_id': core_id,
                 'x': center_x, # Target
                 'y': center_y, # Target
                 'start_x': x_start,
                 'start_y': y_pos,
                 'end_x': x_end,
                 'end_y': y_pos + core_box_height
             })

    def add_process(self):
        """Adds a new process from the input fields."""
        if self.simulation_running:
             messagebox.showwarning("Warning", "Cannot add processes during simulation.")
             return
        try:
            arrival_time = int(self.arrival_time_entry.get())
            burst_time = int(self.burst_time_entry.get())
            if arrival_time < 0 or burst_time <= 0:
                raise ValueError("Arrival time must be >= 0 and Burst time must be > 0.")

            self.process_counter += 1
            new_process = Process(self.process_counter, arrival_time, burst_time, self.canvas, self._get_next_color())
            self.processes.append(new_process)
            self.process_listbox.insert(tk.END, repr(new_process))

            self.arrival_time_entry.delete(0, tk.END)
            self.arrival_time_entry.insert(0, str(arrival_time + 1))
            self.burst_time_entry.delete(0, tk.END)
            self.burst_time_entry.insert(0, str(random.randint(3, 8))) # Suggest


        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")

    def update_speed(self, val):
        """Updates the animation speed factor from the scale."""
        self.animation_speed_factor = float(val)

    def get_delay(self):
        """Calculates the actual delay based on speed factor."""
        return int(ANIMATION_STEP_DELAY_MS * self.animation_speed_factor)

    def toggle_pause(self):
        """Pauses or resumes the simulation."""
        if not self.simulation_running:
            return
        self.simulation_paused = not self.simulation_paused
        if self.simulation_paused:
            self.pause_button.config(text="Resume")
        else:
            self.pause_button.config(text="Pause")
            self.simulasi_langkah()

    def reset_simulation(self):
        """Resets the simulation state and GUI."""
        if hasattr(self, 'animation_id') and self.animation_id:
            self.master.after_cancel(self.animation_id) # Stop

        for p in self.processes:
            p.destroy_visual()
        self.processes = []
        self.ready_queue.clear()
        self.terminated_processes = []
        self.gantt_data = []
        self.cores = [] # Will

        self.current_time = 0
        self.simulation_running = False
        self.simulation_paused = False
        self.process_counter = 0
        self.color_index = 0

        self.time_label.config(text="Time: 0")
        self.process_listbox.delete(0, tk.END)
        self.canvas.delete("process") # Clear
        self.canvas.delete("gantt")   # Clear
        self.results_label.config(text="Waiting for simulation end...")
        self.start_button.config(state=tk.NORMAL)
        self.add_process_button.config(state=tk.NORMAL)
        self.pause_button.config(text="Pause", state=tk.DISABLED)
        self.num_cores_spinbox.config(state=tk.NORMAL)
        self.time_quantum_spinbox.config(state=tk.NORMAL)

        self._draw_simulation_areas()
        self._update_core_display() # Redraw

    def start_simulation(self):
        """Starts the scheduling simulation."""
        if not self.processes:
            messagebox.showwarning("No Processes", "Please add at least one process.")
            return
        if self.simulation_running:
             messagebox.showwarning("Running", "Simulation is already running. Reset first.")
             return

        try:
            self.time_quantum = int(self.time_quantum_spinbox.get())
            self.num_cores = int(self.num_cores_spinbox.get()) # Ensure
            if self.time_quantum <= 0:
                raise ValueError("Time quantum must be positive.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid simulation parameters: {e}")
            return

        self.simulation_running = True
        self.simulation_paused = False

        self.processes.sort(key=lambda p: p.arrival_time) # Sort
        self.terminated_processes = []
        self.ready_queue.clear()
        self.gantt_data = []
        self.current_time = 0
        self.time_label.config(text="Time: 0")
        self.results_label.config(text="Simulation running...")

        initial_x = 50
        initial_y = QUEUE_AREA_Y_START - 30 # Position
        for p in self.processes:
            p.remaining_burst_time = p.burst_time
            p.start_time = -1
            p.completion_time = -1
            p.waiting_time = 0
            p.turnaround_time = 0
            p.state = "New"
            p.current_core = None
            p.time_on_core_current_quantum = 0
            p.destroy_visual() # Clear

        for core in self.cores:
            core['state'] = 'Idle'
            core['process'] = None
            self.canvas.itemconfig(core['visual_id'], fill="lightblue")

        self.start_button.config(state=tk.DISABLED)
        self.add_process_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.num_cores_spinbox.config(state=tk.DISABLED)
        self.time_quantum_spinbox.config(state=tk.DISABLED)

        self.animation_queue = collections.deque() # Queue
        self.simulasi_langkah()


    def _get_queue_position(self, index):
        """Calculates the visual position for a process in the ready queue."""
        x = 50 + (index * (PROCESS_RADIUS * 2 + 10))
        y = QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT / 2
        max_per_row = (CANVAS_WIDTH - 100) // (PROCESS_RADIUS * 2 + 10)
        row = index // max_per_row
        col = index % max_per_row
        x = 50 + (col * (PROCESS_RADIUS * 2 + 10))
        y = QUEUE_AREA_Y_START + 30 + (row * (PROCESS_RADIUS * 2 + 10))
        return x, y

    def _animate_move(self, process, target_x, target_y, steps=ANIMATION_MOVE_STEPS, callback=None):
        """Animates the movement of a process visual smoothly."""
        if not process.visual_id: # Process
            if callback: callback()
            return

        start_x, start_y = process.current_x, process.current_y
        dx = (target_x - start_x) / steps
        dy = (target_y - start_y) / steps
        process.target_x = target_x
        process.target_y = target_y

        def step_move(current_step):
            if self.simulation_paused:
                self.animation_id = self.master.after(100, lambda: step_move(current_step))
                return

            if not process.visual_id:
                if callback: callback()
                return

            if current_step < steps:
                if process.target_x != target_x or process.target_y != target_y:
                    print(f"P{process.id} target changed during move, stopping.")
                    if callback: callback()
                    return

                process.move_visual(dx, dy)
                self.animation_id = self.master.after(max(10, self.get_delay() // steps), lambda: step_move(current_step + 1))
            else:
                process.set_position(target_x, target_y)
                if callback:
                    callback()

        step_move(0)


    def _update_ready_queue_visuals(self, animated_process=None, target_x=None, target_y=None, callback=None):
        """Rearranges visuals in the ready queue area."""
        q_idx = 0
        processes_to_animate = []

        processes_in_queue_area = []
        for p in self.processes:
            if p.visual_id and p.state == "Ready":
                 if QUEUE_AREA_Y_START < p.current_y < QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT + PROCESS_RADIUS*2:
                     processes_in_queue_area.append(p)

        processes_in_queue_area.sort(key=lambda p: p.current_x)

        for p in processes_in_queue_area:
             if p == animated_process and target_x is not None:
                  continue
             target_q_x, target_q_y = self._get_queue_position(q_idx)
             if abs(p.current_x - target_q_x) > 1 or abs(p.current_y - target_q_y) > 1:
                 processes_to_animate.append({'process': p, 'target_x': target_q_x, 'target_y': target_q_y})
             q_idx += 1
        if animated_process and target_x is not None:
             final_q_x, final_q_y = self._get_queue_position(q_idx)
             processes_to_animate.append({'process': animated_process, 'target_x': final_q_x, 'target_y': final_q_y})


        if not processes_to_animate:
            if callback: callback()
            return

        remaining_animations = len(processes_to_animate)

        def on_single_animation_done():
            nonlocal remaining_animations
            remaining_animations -= 1
            if remaining_animations == 0 and callback:
                callback()

        for anim_info in processes_to_animate:
            self._animate_move(anim_info['process'], anim_info['target_x'], anim_info['target_y'], steps=max(3, ANIMATION_MOVE_STEPS // 2), callback=on_single_animation_done)



    def simulasi_langkah(self):
        """Performs one time unit step of the simulation."""
        if not self.simulation_running:
            return

        if self.simulation_paused:
            self.animation_id = self.master.after(200, self.simulasi_langkah)
            return

        current_step_actions = []

        newly_arrived = []
        for process in self.processes:
            if process.state == "New" and process.arrival_time <= self.current_time:
                process.state = "Ready"
                self.ready_queue.append(process)
                newly_arrived.append(process)
                initial_x, initial_y = self._get_queue_position(len(self.ready_queue) + 5) # Place
                initial_y = QUEUE_AREA_Y_START - 30 # Place
                process.create_visual(initial_x, initial_y)
                current_step_actions.append({'type': 'arrive', 'process': process})


        cores_freed_this_step = []
        processes_to_queue = []

        for core in self.cores:
            if core['state'] == 'Busy':
                process = core['process']
                if process: # Should
                    if self.gantt_data and self.gantt_data[-1][0] == process.id and self.gantt_data[-1][1] == core['id'] and self.gantt_data[-1][3] == self.current_time :
                         self.gantt_data[-1] = (process.id, core['id'], self.gantt_data[-1][2], self.current_time + 1)
                    elif not self.gantt_data or self.gantt_data[-1][0] != process.id or self.gantt_data[-1][1] != core['id'] or self.gantt_data[-1][3] != self.current_time:
                         self.gantt_data.append([process.id, core['id'], self.current_time, self.current_time + 1]) # Start

                    process.remaining_burst_time -= 1
                    process.time_on_core_current_quantum += 1

                    if process.remaining_burst_time <= 0:
                        process.state = "Terminated"
                        process.completion_time = self.current_time + 1
                        process.turnaround_time = process.completion_time - process.arrival_time
                        self.terminated_processes.append(process)

                        current_step_actions.append({'type': 'terminate', 'process': process, 'core_id': core['id']})
                        cores_freed_this_step.append(core['id'])
                        core['process'] = None # Clear


                    elif process.time_on_core_current_quantum >= self.time_quantum:
                        process.state = "Ready"
                        process.time_on_core_current_quantum = 0 # Reset
                        processes_to_queue.append(process) # Will

                        current_step_actions.append({'type': 'return_to_queue', 'process': process, 'core_id': core['id']})
                        cores_freed_this_step.append(core['id'])
                        core['process'] = None # Clear

        processes_assigned_this_step = []
        idle_cores = [c for c in self.cores if c['state'] == 'Idle' or c['id'] in cores_freed_this_step]

        while idle_cores and self.ready_queue:
            core = idle_cores.pop(0)
            process_to_run = self.ready_queue.popleft()

            process_to_run.state = "Running"
            process_to_run.current_core = core['id']
            process_to_run.time_on_core_current_quantum = 0 # Start
            if process_to_run.start_time == -1: # First
                process_to_run.start_time = self.current_time

            core['state'] = 'Busy' # Mark
            core['process'] = process_to_run
            processes_assigned_this_step.append({'process': process_to_run, 'core': core})

            current_step_actions.append({'type': 'assign_to_core', 'process': process_to_run, 'core': core})

        for process in processes_to_queue:
             self.ready_queue.append(process)


        for process in self.ready_queue:
             if process.visual_id and QUEUE_AREA_Y_START < process.current_y < QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT + PROCESS_RADIUS*2 :
                  process.waiting_time += 1


        self.execute_animations(current_step_actions, cores_freed_this_step, processes_assigned_this_step)


    def execute_animations(self, actions, freed_core_ids, assigned_actions_info):
        """ Coordinates and executes the animations for the current time step."""

        pending_animations = len(actions)
        if not pending_animations: # If
            self.proceed_to_next_step()
            return

        def on_animation_complete():
            nonlocal pending_animations
            pending_animations -= 1
            if pending_animations == 0:
                self.finalize_step_state(freed_core_ids, assigned_actions_info)
                self.proceed_to_next_step()


        arrival_actions = [a for a in actions if a['type'] == 'arrive']
        assign_actions = [a for a in actions if a['type'] == 'assign_to_core']
        return_actions = [a for a in actions if a['type'] == 'return_to_queue']
        terminate_actions = [a for a in actions if a['type'] == 'terminate']

        for action in terminate_actions:
            process = action['process']
            core_id = action['core_id']
            process.destroy_visual()
            core = next((c for c in self.cores if c['id'] == core_id), None)
            if core:
                 pass # Defer
            on_animation_complete() # Termination


        return_targets = [] # Store
        for action in return_actions:
            process = action['process']
            core = next((c for c in self.cores if c['id'] == action['core_id']), None)
            mid_queue_x = CANVAS_WIDTH / 2
            mid_queue_y = QUEUE_AREA_Y_START + QUEUE_AREA_HEIGHT / 2
            return_targets.append({'process': process, 'target_x': mid_queue_x, 'target_y': mid_queue_y})
            self._animate_move(process, mid_queue_x, mid_queue_y, callback=on_animation_complete)


        for action in assign_actions:
            process = action['process']
            core = action['core']
            target_x, target_y = core['x'], core['y']
            self._animate_move(process, target_x, target_y, callback=on_animation_complete)



        arrivals_returns_pending = len(arrival_actions) + len(return_actions)
        if arrivals_returns_pending == 0 and len(assign_actions) > 0: # Only
             pass # Assign
        elif arrivals_returns_pending == 0 and len(terminate_actions) > 0:
             pass # Terminate
        elif arrivals_returns_pending == 0: # No
             pass # Already

        def on_arrival_return_move_done():
             nonlocal arrivals_returns_pending
             arrivals_returns_pending -= 1
             if arrivals_returns_pending == 0:
                 animated_p = return_targets[0]['process'] if return_targets else None # Pass
                 target_x = return_targets[0]['target_x'] if return_targets else None
                 target_y = return_targets[0]['target_y'] if return_targets else None

                 self._update_ready_queue_visuals(
                     animated_process=animated_p,
                     target_x=target_x,
                     target_y=target_y,
                     callback=None # The
                 )

        for action in arrival_actions:
             process = action['process']
             temp_q_x, temp_q_y = self._get_queue_position(len(self.ready_queue)-1) # Approximate
             self._animate_move(process, temp_q_x, temp_q_y, callback=on_arrival_return_move_done)

        for _ in return_actions:
             on_arrival_return_move_done() # Decrement


    def finalize_step_state(self, freed_core_ids, assigned_actions_info):
        """Update core visual states after animations for the step are done."""
        for core_id in freed_core_ids:
            core = next((c for c in self.cores if c['id'] == core_id), None)
            if core and core.get('process') is None: # Ensure
                core['state'] = 'Idle'
                self.canvas.itemconfig(core['visual_id'], fill="lightblue")

        for assign_info in assigned_actions_info:
            core = assign_info['core']
            core['state'] = 'Busy' # Logical
            self.canvas.itemconfig(core['visual_id'], fill="lightcoral")


    def proceed_to_next_step(self):
        """Checks if simulation is over and schedules the next step."""
        if len(self.terminated_processes) == len(self.processes):
            self.end_simulation()
            return

        self.current_time += 1
        self.time_label.config(text=f"Time: {self.current_time}")

        self.animation_id = self.master.after(self.get_delay(), self.simulasi_langkah)


    def end_simulation(self):
        """Finalizes the simulation and displays results."""
        self.simulation_running = False
        self.pause_button.config(state=tk.DISABLED)
        self.reset_button.config(state=tk.NORMAL) # Allow


        messagebox.showinfo("Simulation Complete", f"Simulation finished at time {self.current_time}.")

        total_waiting_time = 0
        total_turnaround_time = 0
        total_burst_time = 0
        total_busy_time = 0 # Across

        if not self.processes: return # Avoid

        for p in self.terminated_processes:
             p.turnaround_time = p.completion_time - p.arrival_time
             p.waiting_time = p.turnaround_time - p.burst_time
             total_waiting_time += p.waiting_time
             total_turnaround_time += p.turnaround_time
             total_burst_time += p.burst_time # Sum

        avg_waiting_time = total_waiting_time / len(self.processes)
        avg_turnaround_time = total_turnaround_time / len(self.processes)

        for entry in self.gantt_data:
            total_busy_time += (entry[3] - entry[2])

        if self.current_time > 0 and self.num_cores > 0:
             total_possible_time = self.current_time * self.num_cores
             cpu_utilization = (total_busy_time / total_possible_time) * 100 if total_possible_time > 0 else 0
        else:
             cpu_utilization = 0


        result_text = (
            f"Average Waiting Time: {avg_waiting_time:.2f}\n"
            f"Average Turnaround Time: {avg_turnaround_time:.2f}\n"
            f"CPU Utilization: {cpu_utilization:.2f}%"
        )
        self.results_label.config(text=result_text)

        self.draw_gantt_chart()


    def draw_gantt_chart(self):
        """Draws the Gantt chart on the canvas."""
        self.canvas.delete("gantt") # Clear

        if not self.gantt_data:
            return

        chart_x_start = 50
        chart_y_start = self.gantt_y_start # Use
        bar_height = 20
        time_scale = 15 # Pixels
        max_time = self.current_time
        padding = 5

        needed_width = chart_x_start + max_time * time_scale + 50
        needed_height = chart_y_start + (self.num_cores + 1) * (bar_height + padding) # Add
        current_scroll_region = list(map(int, self.canvas.cget("scrollregion").split()))
        new_scroll_width = max(current_scroll_region[2], needed_width)
        new_scroll_height = max(current_scroll_region[3], needed_height)
        self.canvas.config(scrollregion=(0, 0, new_scroll_width, new_scroll_height))


        self.canvas.create_line(chart_x_start, chart_y_start + (self.num_cores + 0.5) * (bar_height + padding) ,
                                chart_x_start + max_time * time_scale, chart_y_start + (self.num_cores + 0.5) * (bar_height + padding),
                                tags="gantt")
        for t in range(max_time + 1):
            x = chart_x_start + t * time_scale
            self.canvas.create_line(x, chart_y_start + (self.num_cores + 0.5) * (bar_height + padding) - 3,
                                    x, chart_y_start + (self.num_cores + 0.5) * (bar_height + padding) + 3, tags="gantt")
            if t % 5 == 0 or t == max_time: # Label
                 self.canvas.create_text(x, chart_y_start + (self.num_cores + 0.5) * (bar_height + padding) + 10, text=str(t), anchor="n", tags="gantt")


        process_map = {p.id: p for p in self.processes} # Map

        for core_id in range(self.num_cores):
            y = chart_y_start + core_id * (bar_height + padding)
            self.canvas.create_text(chart_x_start - 10, y + bar_height / 2, text=f"C{core_id}", anchor="e", tags="gantt")

            core_gantt_data = sorted([g for g in self.gantt_data if g[1] == core_id], key=lambda x: x[2]) # Sort

            for entry in core_gantt_data:
                p_id, _, start, end = entry
                process = process_map.get(p_id)
                color = process.color if process else "gray" # Fallback

                x1 = chart_x_start + start * time_scale
                x2 = chart_x_start + end * time_scale
                self.canvas.create_rectangle(x1, y, x2, y + bar_height, fill=color, outline="black", tags="gantt")
                if (x2 - x1) > 15: # Only
                    self.canvas.create_text((x1 + x2) / 2, y + bar_height / 2, text=f"P{p_id}", fill="white", tags="gantt", font=("Arial", 8))

if __name__ == "__main__":
    root = tk.Tk()
    app = RRSchedulerApp(root)
    root.mainloop()
