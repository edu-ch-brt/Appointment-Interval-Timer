import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import time
import threading
import pygame
import os
from math import pi, sin, cos

class IntervalTimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Appointment Timer")
        self.root.geometry("600x670")
        self.root.minsize(600, 670)  # Set minimum size to prevent cutting off content

        # Initialize pygame for sound
        pygame.mixer.init()
        
        # Set sound file path - assuming it always exists
        self.sound_file = os.path.join(os.path.dirname(__file__), "bell.wav")
        
        # Timer state
        self.running = False
        self.waiting_for_start = False
        self.thread = None
        self.start_time = None
        self.duration_minutes = None
        self.current_progress = 0
        
        # Create UI elements
        self.create_widgets()
    
    def create_widgets(self):
        # Create a style to use for the frames (no border)
        style = ttk.Style()
        style.configure('TFrame', borderwidth=0)
        style.configure('TLabelframe', borderwidth=1)
        style.configure('TLabelframe.Label', font=('Arial', 10))
        
        # Main frame with direct content (no scrolling)
        main_frame = ttk.Frame(self.root, padding="5", style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current time at the top
        self.time_display = tk.StringVar(value="Current Time: " + datetime.datetime.now().strftime("%I:%M:%S %p"))
        ttk.Label(main_frame, textvariable=self.time_display, font=("Arial", 10, "bold")).pack(pady=2)
        
        # Time selection frame - reduce padding
        time_frame = ttk.LabelFrame(main_frame, text="Set First Appointment Start Time", padding="5")
        time_frame.pack(fill=tk.X, pady=5)
        
        # Add a time selection frame with more space
        time_grid = ttk.Frame(time_frame)
        time_grid.pack(padx=5, pady=2)
        
        # Hour selection
        ttk.Label(time_grid, text="Hour:").grid(row=0, column=0, padx=5, pady=2)
        self.hour_var = tk.StringVar(value=datetime.datetime.now().strftime("%I"))
        hour_spinner = ttk.Spinbox(time_grid, from_=1, to=12, width=5, textvariable=self.hour_var)
        hour_spinner.grid(row=0, column=1, padx=5, pady=2)
        
        # Minute selection
        ttk.Label(time_grid, text="Minute:").grid(row=0, column=2, padx=5, pady=2)
        self.minute_var = tk.StringVar(value=datetime.datetime.now().strftime("%M"))
        minute_spinner = ttk.Spinbox(time_grid, from_=0, to=59, width=5, textvariable=self.minute_var)
        minute_spinner.grid(row=0, column=3, padx=5, pady=2)
        
        # AM/PM selection
        ttk.Label(time_grid, text="AM/PM:").grid(row=0, column=4, padx=5, pady=2)
        self.ampm_var = tk.StringVar(value=datetime.datetime.now().strftime("%p"))
        ampm_combobox = ttk.Combobox(time_grid, values=["AM", "PM"], width=5, textvariable=self.ampm_var)
        ampm_combobox.grid(row=0, column=5, padx=5, pady=2)
        ampm_combobox.state(["readonly"])
        
        # Duration frame - reduce padding
        duration_frame = ttk.LabelFrame(main_frame, text="Set Appointment Duration", padding="5")
        duration_frame.pack(fill=tk.X, pady=5)
        
        # Duration container for better spacing
        duration_container = ttk.Frame(duration_frame)
        duration_container.pack(padx=5, pady=2)
        
        # Duration selection
        ttk.Label(duration_container, text="Duration (minutes):").grid(row=0, column=0, padx=5, pady=2)
        self.duration_var = tk.StringVar(value="4")
        duration_spinner = ttk.Spinbox(duration_container, from_=1, to=60, width=5, textvariable=self.duration_var)
        duration_spinner.grid(row=0, column=1, padx=5, pady=2)
        
        # Canvas for circle visualization - make it smaller
        canvas_frame = ttk.LabelFrame(main_frame, text="Timer Progress", padding="3")
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        
        # Countdown timer above the circle
        self.countdown_var = tk.StringVar(value="Next Appointment: --:--")
        ttk.Label(canvas_frame, textvariable=self.countdown_var, font=("Arial", 12, "bold")).pack(pady=2)
        
        self.canvas = tk.Canvas(canvas_frame, width=350, height=320, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)
        
        # Bind resize event for the circle
        def resize_circle(event):  # pylint: disable=unused-argument
            # Get the new dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # Calculate new radius and center
            self.radius = min(width, height) // 2 - 20  # 20px margin
            self.center_x = width // 2
            self.center_y = height // 2
            
            # Redraw the circle outline
            self.canvas.delete("all")
            self.circle_outline = self.canvas.create_oval(
                int(self.center_x - self.radius),
                int(self.center_y - self.radius),
                int(self.center_x + self.radius),
                int(self.center_y + self.radius),
                outline="black",
                width=2
            )
            
            # Redraw progress if needed
            if hasattr(self, 'current_progress'):
                self.update_circle(self.current_progress)
        
        self.canvas.bind("<Configure>", resize_circle)
        
        # Draw empty circle with smaller radius
        self.center_x, self.center_y = 175, 175
        self.radius = 125
        self.circle_outline = self.canvas.create_oval(
            int(self.center_x - self.radius),
            int(self.center_y - self.radius),
            int(self.center_x + self.radius),
            int(self.center_y + self.radius),
            outline="black",
            width=2
        )
        
        # Status display with visual indicator
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=2)
        
        self.status_var = tk.StringVar(value="Status: Ready")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Visual indicator
        self.indicator_canvas = tk.Canvas(status_frame, width=20, height=20, bg="white", highlightthickness=0)
        self.indicator_canvas.pack(side=tk.LEFT, padx=5)
        self.indicator = self.indicator_canvas.create_oval(2, 2, 18, 18, fill="gray", outline="black")
        
        # Blink state
        self.blink_state = False
        
        # Add a status label to clearly indicate when timer is waiting
        self.timer_active_label = ttk.Label(
            main_frame, 
            text="Timer Inactive", 
            font=("Arial", 10, "bold"),
            foreground="gray"
        )
        self.timer_active_label.pack(pady=2)
        
        # Control buttons with more compact layout
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(button_frame, text="Start Timer", command=self.start_timer)
        self.start_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Timer", command=self.stop_timer, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10, expand=True)
        
        self.exit_button = ttk.Button(button_frame, text="Exit", command=self.exit_application)
        self.exit_button.pack(side=tk.RIGHT, padx=10, expand=True)
        
        # Remove content_canvas binding that might cause scrollbar issues
        self.root.unbind_all("<MouseWheel>")
        
        # Update time display every second
        self.update_time()
    
    def update_time(self):
        """Update the current time display"""
        current_time = datetime.datetime.now()
        self.time_display.set("Current Time: " + current_time.strftime("%I:%M:%S %p"))
        self.root.after(1000, self.update_time)
    
    def update_countdown(self, target_time):
        """Update the countdown display until the target time"""
        if not self.running:
            self.countdown_var.set("Next Alert: --:--")
            return
            
        now = datetime.datetime.now()
        if target_time <= now:
            self.countdown_var.set("Next Appointment!")
            return
            
        # Calculate time difference using total_seconds for accuracy
        time_diff = target_time - now
        total_seconds = time_diff.total_seconds()
        
        # Format as HH:MM:SS
        hours, remainder = divmod(int(total_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Format countdown display - show hours only if non-zero
        if hours > 0:
            self.countdown_var.set(f"Next Appointment: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.countdown_var.set(f"Next Appointment: {minutes:02d}:{seconds:02d}")
        
        # Schedule next update - only if still running to avoid recursion issues
        if self.running:
            # Use a fixed value to avoid closure issues
            self.root.after(1000, lambda t=target_time: self.update_countdown(t))
    
    def start_timer(self):
        """Start the timer"""
        if self.running:
            messagebox.showinfo("Already Running", "Timer is already running!")
            return
        
        try:
            # Parse input values
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            ampm = self.ampm_var.get()
            self.duration_minutes = int(self.duration_var.get())
            
            # Validate inputs
            if hour < 1 or hour > 12:
                raise ValueError("Hour must be between 1 and 12")
            if minute < 0 or minute > 59:
                raise ValueError("Minute must be between 0 and 59")
            if ampm not in ["AM", "PM"]:
                raise ValueError("AM/PM selection is invalid")
            if self.duration_minutes < 1:
                raise ValueError("Duration must be at least 1 minute")
            
            # Convert to 24-hour format
            if ampm == "PM" and hour < 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0
            
            # Set start time for today
            now = datetime.datetime.now()
            self.start_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If start time has already passed today, set it for tomorrow
            if self.start_time < now:
                self.start_time += datetime.timedelta(days=1)
            
            # Start the timer thread
            self.running = True
            self.status_var.set(f"Status: Timer set for {self.start_time.strftime('%I:%M %p')}")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Update active indicator
            self.timer_active_label.config(text="Timer Active - Waiting for Start Time", foreground="green")
            self.indicator_canvas.itemconfig(self.indicator, fill="green")
            
            self.thread = threading.Thread(target=self.timer_thread, daemon=True)
            self.thread.start()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
    
    def timer_thread(self):
        """Background thread for timer operation"""
        try:
            # Ensure start_time is set
            if self.start_time is None:
                now = datetime.datetime.now()
                self.start_time = now + datetime.timedelta(seconds=10)
                
            # Ensure duration_minutes is set
            if self.duration_minutes is None:
                self.duration_minutes = 4  # Default to 4 minutes

            # Start blinking the indicator during waiting period
            self.waiting_for_start = True
            self.root.after(0, self.start_indicator_blink)
            
            # Wait until start time
            now = datetime.datetime.now()
            if now < self.start_time:
                self.status_var.set(f"Status: Waiting until {self.start_time.strftime('%I:%M %p')}")
                
                # Start countdown to start time - using fixed value to avoid closure issues
                start_time_snapshot = self.start_time
                self.root.after(0, lambda st=start_time_snapshot: self.update_countdown(st))
                
                # Wait until start time, checking periodically to allow for clean shutdown
                while now < self.start_time and self.running:
                    time_to_wait = min(1.0, (self.start_time - now).total_seconds())
                    if time_to_wait <= 0:
                        break
                    time.sleep(time_to_wait)
                    now = datetime.datetime.now()
                
                # Exit if timer was stopped while waiting
                if not self.running:
                    return
            
            # Timer has started - stop blinking and set solid green
            self.waiting_for_start = False
            # Use the main thread for UI updates
            self.root.after(0, lambda: self.indicator_canvas.itemconfig(self.indicator, fill="green"))
            self.root.after(0, lambda: self.status_var.set("Status: Timer active"))
            self.root.after(0, lambda: self.timer_active_label.config(text="Timer Active - Running", foreground="green"))
            
            # Play first alert at start time
            self.play_alert()
            
            # Set next alert time
            next_alert = self.start_time
            
            # Main timer loop
            while self.running:
                # Calculate next alert time
                next_alert += datetime.timedelta(minutes=self.duration_minutes)
                
                # Start countdown to next alert - using fixed value to avoid closure issues
                current_next_alert = next_alert
                self.root.after(0, lambda na=current_next_alert: self.update_countdown(na))
                
                # Calculate time until next alert
                now = datetime.datetime.now()
                time_until_next = (next_alert - now).total_seconds()
                
                # Handle case where we're behind schedule
                if time_until_next <= 0:
                    # Limit how many catch-up alerts we'll do (max 5)
                    catch_up_count = 0
                    while time_until_next <= 0 and catch_up_count < 5 and self.running:
                        # Play alert immediately if we're behind schedule
                        self.play_alert()
                        next_alert += datetime.timedelta(minutes=self.duration_minutes)
                        now = datetime.datetime.now()
                        time_until_next = (next_alert - now).total_seconds()
                        catch_up_count += 1
                    continue
                
                # Update the circle progress in small increments
                update_interval = 0.1  # seconds
                steps = int(time_until_next / update_interval)
                
                for i in range(steps):
                    if not self.running:
                        break 
                    
                    # Update progress circle
                    progress = i / steps
                    self.update_circle(progress)
                    
                    # Sleep for the update interval
                    time.sleep(update_interval)
                
                if self.running:
                    # Play alert at scheduled time
                    self.play_alert()
            
        except Exception as e:
            print(f"Error in timer thread: {e}")
        finally:
            # Ensure UI is reset when thread ends
            if self.running:
                self.root.after(0, self.reset_ui)
    
    def start_indicator_blink(self):
        """Start blinking the indicator to show the timer is running"""
        if not self.running:
            return
            
        # Only blink if we're waiting for the start time
        if self.waiting_for_start:
            # Toggle the blink state
            self.blink_state = not self.blink_state
            
            # Update indicator color
            if self.blink_state:
                self.indicator_canvas.itemconfig(self.indicator, fill="green")
            else:
                self.indicator_canvas.itemconfig(self.indicator, fill="light green")
                
            # Schedule the next blink
            self.root.after(500, self.start_indicator_blink)
    
    def update_circle(self, progress):
        """Update the circle fill based on progress (0.0 to 1.0)"""
        self.canvas.delete("progress")
        self.current_progress = progress
        
        if progress <= 0:
            return
        
        # Draw filled portion of circle
        angle = 360 * progress
        
        # Use a slightly smaller radius for the filling (95% of the outline radius)
        fill_radius = self.radius * 0.95
        
        # Create a filled arc using a polygon
        points = [self.center_x, self.center_y]
        
        # Add points around the arc
        for i in range(0, int(angle) + 1, 1):
            rad_i = i * (pi / 180)
            x = self.center_x + fill_radius * sin(rad_i)
            y = self.center_y - fill_radius * cos(rad_i)
            points.extend([x, y])
        
        # Draw the filled polygon
        if len(points) > 4:  # Need at least 3 points to make a polygon (plus the center point)
            self.canvas.create_polygon(points, fill="light blue", outline="", tags="progress")
    
    def play_alert(self):
        """Play the alert sound"""
        try:
            # Play sound from the bell.wav file
            pygame.mixer.music.load(self.sound_file)
            pygame.mixer.music.play()
            
            # Flash the circle for visual feedback
            original_color = self.canvas.itemcget(self.circle_outline, "outline")
            # Use integers for width values
            self.canvas.itemconfig(self.circle_outline, outline="red", width=4)
            self.root.after(500, lambda: self.canvas.itemconfig(self.circle_outline, outline=original_color, width=2))
            
        except Exception as e:
            print(f"Error playing alert: {e}")
    
    def stop_timer(self):
        """Stop the timer without exiting the application"""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            # Let the thread finish naturally with a reasonable timeout
            self.status_var.set("Status: Stopping timer...")
            self.thread.join(0.5)  # Give it a bit more time to clean up
        
        # Reset UI elements
        self.reset_ui()
        messagebox.showinfo("Timer Stopped", "Timer has been stopped. You can adjust settings and start again.")
    
    def exit_application(self):
        """Exit the application"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(0.5)  # Give it a bit more time to clean up
        
        # Clean up pygame resources
        try:
            pygame.mixer.quit()
        except:
            pass
                
        self.root.destroy()
    
    def reset_ui(self):
        """Reset the UI elements"""
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
    root = tk.Tk()
    IntervalTimerApp(root)  # No need to store reference if not used
    root.mainloop()

if __name__ == "__main__":
    main()