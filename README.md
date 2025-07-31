![App Icon](https://github.com/cheamsteve/Appointment-Interval-Timer/blob/c07937c9ae3cb6c1f14988f6e430dbf933233a16/interval.png)
# Appointment Interval Timer

The application allows a user to set a start time and a recurring interval duration. Once started, the program waits until the specified start time, plays an initial sound alert, and then continues to play the alert at each subsequent interval.

#### Core Features
- GUI built with Python's standard Tkinter library.
- Sound alerts handled by the Pygame library.
- Timer logic runs in a background thread to keep the UI responsive.
- Visual feedback including a countdown to the next alert, a circular progress bar, and a blinking status indicator.
- User inputs for start time (12-hour format with AM/PM) and interval duration (in minutes) are validated.

#### GUI
It uses modern ttk themed widgets for a clean user interface where the user can easily set a start time and a repeating duration.

#### Threading
The application correctly uses a separate threading.Thread for the main timer loop. This is excellent practice as it prevents the user interface from freezing while the program waits for the next alert time.

#### Error Handling
It includes basic validation to catch incorrect user inputs, preventing crashes from invalid time or duration values.
