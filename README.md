# Multicore Round Robin Scheduler with GUI and Animation

This project implements a simulation of **Round Robin scheduling** for processes on a **multicore system**. The application provides a **Graphical User Interface (GUI)** with **animation** to visualize how processes are scheduled and executed across multiple cores. It helps demonstrate the scheduling algorithm's behavior in real-time.

## Key Features
- **Round Robin Scheduling Algorithm** to manage process execution on multicore systems.
- Supports up to **8 CPU cores** for simulation.
- User input for configuring **Time Quantum** and process details (Process ID, Arrival Time, and Burst Time).
- Real-time **process animation** with colored particles representing processes as they are scheduled to cores.
- **Gantt Chart** displaying the execution timeline of processes.
- **Performance statistics** including **Average Waiting Time**, **Turnaround Time**, and **CPU Utilization**.

## Installation

1. Ensure you have **Python 3.x** installed on your system.
2. Install required Python libraries:
   ```bash
   pip install tkinter
   ```

3. Run the simulation with:
   ```bash
   python rr-multicore-visualizer.py
   ```

## How It Works
The program uses a **Round Robin scheduling algorithm** where processes are assigned to cores in a cyclic manner, with each process getting a **time quantum** for execution. The processes are visualized as animated particles moving between the ready queue and the cores. The application calculates and displays various performance metrics like waiting time, turnaround time, and CPU utilization.

## Screenshots
> ![image](https://github.com/user-attachments/assets/951e2aa7-2150-406a-a7ec-345d79c30085)

> ![image](https://github.com/user-attachments/assets/84f54188-460b-4a01-bc61-8ea76b85177f)

> ![image](https://github.com/user-attachments/assets/3061bcfe-6fe4-4381-8108-5a5db98372f3)

> ![image](https://github.com/user-attachments/assets/f1d57415-a0b8-4523-9158-fb8277d524a6)



## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
