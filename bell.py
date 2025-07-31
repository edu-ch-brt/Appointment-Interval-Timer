# Import necessary libraries
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import time
import threading
import pygame
import os
from math import pi, sin, cos

class IntervalTimerApp:
    """
    A class to create a GUI application for an interval timer that plays a sound
    at specified intervals after a set start time.
    """
    def __init__(self, root):
        """Initializes the application window and state variables."""
        self.root = root
        self.root.title("Appointment Timer")
        self.root.geometry("600x670")
        self.root.minsize(600, 670)  # Prevent the window from being too small

        # Initialize pygame's mixer for sound playback
        pygame.mixer.init()
        
        # Define the path to the sound file, assuming it's in the same directory
        self.sound_file = os.path.join(os.path.dirname(__file__), "bell.wav")
        
        # --- State Variables ---
        self.running = False  # Controls the main timer loop
        self.waiting_for_start = False  # True if the timer is waiting for the start time
        self.thread = None  # Holds the timer thread object
        self.start_time = None  # The scheduled start time for the first alert
        self.duration_minutes = None  # The interval duration in minutes
        self.current_progress = 0  # Progress of the circle visualizer (0.0 to 1.0)
        
        # Build the user interface
        self.create_widgets()
    
    def create_widgets(self):
        """Creates and arranges all the GUI elements (widgets) in the window."""
        # --- Styling ---
        style = ttk.Style()
        style.configure('TFrame', borderwidth=0)
        style.configure('TLabelframe', borderwidth=1)
        style.configure('TLabelframe.Label', font=('Arial', 10))
        
        # --- Main Layout Frame ---
        main_frame = ttk.Frame(self.root, padding="5", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Label to display the current system time, updated every second
        self.time_display = tk.StringVar(value="Current Time: " + datetime.datetime.now().strftime("%I:%M:%S %p"))
        ttk.Label(main_frame, textvariable=self.time_display, font=("Arial", 10, "bold")).pack(pady=2)
        
        # --- Start Time Selection ---
        time_frame = ttk.LabelFrame(main_frame, text="Set First Appointment Start Time", padding="5")
        time_frame.pack(fill=tk.X, pady=5)
        
        time_grid = ttk.Frame(time_frame)
        time_grid.pack(padx=5, pady=2)
        
        ttk.Label(time_grid, text="Hour:").grid(row=0, column=0, padx=5, pady=2)
        self.hour_var = tk.StringVar(value=datetime.datetime.now().strftime("%I"))
        hour_spinner = ttk.Spinbox(time_grid, from_=1, to=12, width=5, textvariable=self.hour_var)
        hour_spinner.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(time_grid, text="Minute:").grid(row=0, column=2, padx=5, pady=2)
        self.minute_var = tk.StringVar(value=datetime.datetime.now().strftime("%M"))
        minute_spinner = ttk.Spinbox(time_grid, from_=0, to=59, width=5, textvariable=self.minute_var)
        minute_spinner.grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(time_grid, text="AM/PM:").grid(row=0, column=4, padx=5, pady=2)
        self.ampm_var = tk.StringVar(value=datetime.datetime.now().strftime("%p"))
        ampm_combobox = ttk.Combobox(time_grid, values=["AM", "PM"], width=5, textvariable=self.ampm_var)
        ampm_combobox.grid(row=0, column=5, padx=5, pady=2)
        ampm_combobox.state(["readonly"])  # Prevent user from typing custom values
        
        # --- Duration Selection ---
        duration_frame = ttk.LabelFrame(main_frame, text="Set Appointment Duration", padding="5")
        duration_frame.pack(fill=tk.X, pady=5)
        
        duration_container = ttk.Frame(duration_frame)
        duration_container.pack(padx=5, pady=2)
        
        ttk.Label(duration_container, text="Duration (minutes):").grid(row=0, column=0, padx=5, pady=2)
        self.duration_var = tk.StringVar(value="4")
        duration_spinner = ttk.Spinbox(duration_container, from_=1, to=60, width=5, textvariable=self.duration_var)
        duration_spinner.grid(row=0, column=1, padx=5, pady=2)
        
        # --- Progress Visualization (Circle) ---
        canvas_frame = ttk.LabelFrame(main_frame, text="Timer Progress", padding="3")
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        
        self.countdown_var = tk.StringVar(value="Next Appointment: --:--")
        ttk.Label(canvas_frame, textvariable=self.countdown_var, font=("Arial", 12, "bold")).pack(pady=2)
        
        self.canvas = tk.Canvas(canvas_frame, width=350, height=320, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # This function makes the progress circle responsive to window resizing
        def resize_circle(event):
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # Recalculate radius and center based on the new canvas size
            self.radius = min(width, height) // 2 - 20
            self.center_x = width // 2
            self.center_y = height // 2
            
            # Redraw the circle outline and progress fill
            self.canvas.delete("all")
            self.circle_outline = self.canvas.create_oval(
                int(self.center_x - self.radius), int(self.center_y - self.radius),
                int(self.center_x + self.radius), int(self.center_y + self.radius),
                outline="black", width=2
            )
            if hasattr(self, 'current_progress'):
                self.update_circle(self.current_progress)
        
        self.canvas.bind("<Configure>", resize_circle)
        
        # Draw the initial empty circle outline
        self.center_x, self.center_y = 175, 175
        self.radius = 125
        self.circle_outline = self.canvas.create_oval(
            int(self.center_x - self.radius), int(self.center_y - self.radius),
            int(self.center_x + self.radius), int(self.center_y + self.radius),
            outline="black", width=2
        )
        
        # --- Status Display ---
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=2)
        
        self.status_var = tk.StringVar(value="Status: Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # A small colored dot for visual status indication
        self.indicator_canvas = tk.Canvas(status_frame, width=20, height=20, bg="white", highlightthickness=0)
        self.indicator_canvas.pack(side=tk.LEFT, padx=5)
        self.indicator = self.indicator_canvas.create_oval(2, 2, 18, 18, fill="gray", outline="black")
        self.blink_state = False  # Used to toggle the blinking effect
        
        self.timer_active_label = ttk.Label(
            main_frame, text="Timer Inactive", font=("Arial", 10, "bold"), foreground="gray"
        )
        self.timer_active_label.pack(pady=2)
        
        # --- Control Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Timer", command=self.start_timer)
        self.start_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Timer", command=self.stop_timer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.exit_application)
        self.exit_button.pack(side=tk.RIGHT, padx=10, expand=True)
        
        # Start the clock update loop
        self.update_time()
    
    def update_time(self):
        """Updates the current time label every second."""
        current_time = datetime.datetime.now()
        self.time_display.set("Current Time: " + current_time.strftime("%I:%M:%S %p"))
        # Schedule this method to run again after 1000ms (1 second)
        self.root.after(1000, self.update_time)
    
    def update_countdown(self, target_time):
        """Updates the countdown label to show time remaining until the next alert."""
        if not self.running:
            self.countdown_var.set("Next Alert: --:--")
            return
            
        now = datetime.datetime.now()
        if target_time <= now:
            self.countdown_var.set("Next Appointment!")
            return
            
        time_diff = target_time - now
        total_seconds = time_diff.total_seconds()
        
        # Convert total seconds into HH:MM:SS format
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Display hours only if necessary for a cleaner look
        if hours > 0:
            self.countdown_var.set(f"Next Appointment: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.countdown_var.set(f"Next Appointment: {minutes:02d}:{seconds:02d}")
        
        # Schedule the next update if the timer is still active
        if self.running:
            self.root.after(1000, lambda t=target_time: self.update_countdown(t))
    
    def start_timer(self):
        """Validates user input and starts the timer in a background thread."""
        if self.running:
            messagebox.showinfo("Already Running", "Timer is already running!")
            return
        
        try:
            # --- Input Parsing and Validation ---
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            ampm = self.ampm_var.get()
            self.duration_minutes = int(self.duration_var.get())
            
            if not (1 <= hour <= 12):
                raise ValueError("Hour must be between 1 and 12")
            if not (0 <= minute <= 59):
                raise ValueError("Minute must be between 0 and 59")
            if ampm not in ["AM", "PM"]:
                raise ValueError("AM/PM selection is invalid")
            if self.duration_minutes < 1:
                raise ValueError("Duration must be at least 1 minute")
            
            # Convert 12-hour format to 24-hour for internal calculations
            if ampm == "PM" and hour < 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0  # Midnight case
            
            # --- Set Start Time ---
            now = datetime.datetime.now()
            self.start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If the calculated start time is in the past, schedule it for tomorrow
            if self.start_time < now:
                self.start_time += datetime.timedelta(days=1)
            
            # --- Start Timer Thread ---
            self.running = True
            self.status_var.set(f"Status: Timer set for {self.start_time.strftime('%I:%M %p')}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Update UI to reflect the active state
            self.timer_active_label.config(text="Timer Active - Waiting for Start Time", foreground="green")
            self.indicator_canvas.itemconfig(self.indicator, fill="green")
            
            # A daemon thread will exit automatically when the main program exits
            self.thread = threading.Thread(target=self.timer_thread, daemon=True)
            self.thread.start()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
    
    def timer_thread(self):
        """
        This function runs in a separate thread to handle all timer logic,
        preventing the GUI from freezing.
        """
        try:
            # --- Wait for the specified start time ---
            self.waiting_for_start = True
            self.root.after(0, self.start_indicator_blink)  # Start blinking the indicator
            
            now = datetime.datetime.now()
            if now < self.start_time:
                self.status_var.set(f"Status: Waiting until {self.start_time.strftime('%I:%M %p')}")
                self.root.after(0, lambda: self.update_countdown(self.start_time))
                
                # Sleep in short intervals to allow the loop to be interrupted by the stop button
                while now < self.start_time and self.running:
                    time_to_wait = min(1.0, (self.start_time - now).total_seconds())
                    if time_to_wait <= 0:
                        break
                    time.sleep(time_to_wait)
                    now = datetime.datetime.now()
                
                # Exit if timer was stopped while waiting
                if not self.running:
                    return
            
            # --- Main Timer Loop ---
            self.waiting_for_start = False  # Stop blinking
            # Update UI from the main thread using root.after()
            self.root.after(0, lambda: self.indicator_canvas.itemconfig(self.indicator, fill="green"))
            self.root.after(0, lambda: self.status_var.set("Status: Timer active"))
            self.root.after(0, lambda: self.timer_active_label.config(text="Timer Active - Running", foreground="green"))
            
            self.play_alert()  # Play the first alert at the start time
            next_alert = self.start_time
            
            # This loop runs indefinitely until self.running is set to False
            while self.running:
                next_alert += datetime.timedelta(minutes=self.duration_minutes)
                self.root.after(0, lambda na=next_alert: self.update_countdown(na))
                
                now = datetime.datetime.now()
                time_until_next = (next_alert - now).total_seconds()
                
                # --- Progress Circle Update Loop ---
                # This inner loop smoothly updates the progress circle over the interval duration
                update_interval = 0.1  # Update the circle every 100ms
                steps = int(time_until_next / update_interval)
                
                for i in range(steps):
                    if not self.running:
                        break
                    self.update_circle(i / steps)  # Update progress from 0.0 to 1.0
                    time.sleep(update_interval)
                
                if self.running:
                    self.play_alert()  # Play the alert for the completed interval
            
        except Exception as e:
            print(f"Error in timer thread: {e}")
        finally:
            # Ensure the UI is reset if the thread exits for any reason
            if self.running:
                self.root.after(0, self.reset_ui)
    
    def start_indicator_blink(self):
        """Blinks the status indicator green while waiting for the timer to start."""
        if not self.running or not self.waiting_for_start:
            return  # Stop blinking if timer is stopped or has already started
            
        self.blink_state = not self.blink_state
        color = "green" if self.blink_state else "light green"
        self.indicator_canvas.itemconfig(self.indicator, fill=color)
        self.root.after(500, self.start_indicator_blink)  # Schedule next blink
    
    def update_circle(self, progress):
        """Updates the progress circle fill based on a value from 0.0 to 1.0."""
        self.canvas.delete("progress")  # Clear the previous progress drawing
        self.current_progress = progress
        if progress <= 0:
            return
        
        # Calculate the angle of the arc to draw (360 degrees for full progress)
        angle = 360 * progress
        fill_radius = self.radius * 0.95  # Fill is slightly smaller than the outline
        
        # Create a polygon to represent the filled arc for a smooth, solid appearance
        points = [self.center_x, self.center_y]
        for i in range(0, int(angle) + 1):
            rad_i = i * (pi / 180)  # Convert angle to radians
            x = self.center_x + fill_radius * sin(rad_i)
            y = self.center_y - fill_radius * cos(rad_i)
            points.extend([x, y])
        
        if len(points) > 4:
            self.canvas.create_polygon(points, fill="light blue", outline="", tags="progress")
    
    def play_alert(self):
        """Plays the sound alert and flashes the circle for visual feedback."""
        try:
            pygame.mixer.music.load(self.sound_file)
            pygame.mixer.music.play()
            
            # Flash the circle outline red for 500ms to provide visual feedback
            original_color = self.canvas.itemcget(self.circle_outline, "outline")
            self.canvas.itemconfig(self.circle_outline, outline="red", width=4)
            self.root.after(500, lambda: self.canvas.itemconfig(self.circle_outline, outline=original_color, width=2))
            
        except Exception as e:
            # This can happen if the sound file is missing or corrupt
            print(f"Error playing alert: {e}")
    
    def stop_timer(self):
        """Stops the timer thread and resets the UI to its initial state."""
        if not self.running:
            return
            
        self.running = False  # This will cause the timer_thread loop to terminate
        if self.thread and self.thread.is_alive():
            self.status_var.set("Status: Stopping timer...")
            self.thread.join(0.5)  # Wait briefly for the thread to finish
        
        self.reset_ui()
        messagebox.showinfo("Timer Stopped", "Timer has been stopped.")
    
    def exit_application(self):
        """Stops the timer thread and closes the application gracefully."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(0.5)
        
        pygame.mixer.quit()  # Clean up pygame resources
        self.root.destroy()
    
    def reset_ui(self):
        """Resets all UI elements to their initial, non-running state."""
        self.running = False
        self.waiting_for_start = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Status: Ready")
        self.canvas.delete("progress")
        self.indicator_canvas.itemconfig(self.indicator, fill="gray")
        self.timer_active_label.config(text="Timer Inactive", foreground="gray")
        self.countdown_var.set("Next Alert: --:--")

def main():
    """The main entry point for the application."""
    root = tk.Tk()
    IntervalTimerApp(root)
    root.mainloop()

# This ensures the main() function is called only when the script is executed directly
if __name__ == "__main__":
    main()
