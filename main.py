# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 08:03:01 2024

@author: jeizadi
"""
from datetime import datetime
import math, os
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont


class MaterialMeasurement(tk.Tk):
    def __init__(self):
        super().__init__()
        self.tk_image = None
        self.tk_img = None
        self.image_y = None
        self.image_x = None
        self.offset_y = None
        self.offset_x = None
        self.canvas = None
        self.image = None
        self.image_lot = None
        self.folder_path = None
        self.file_path = None
        self.image_label = None
        self.file = None
        self.image_height = None
        self.image_width = None
        self.zoom_mode = None
        self.zoom_factor = 1.0
        self.title("Measurement Window")
        # Calculate a reasonable size and position for the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.window_width = int(0.8 * screen_width)
        self.window_height = int(0.8 * screen_height)
        x_position = (screen_width - self.window_width) // 2
        y_position = (screen_height - self.window_height) // 2
        # Set the window size and position
        self.geometry(f"{self.window_width}x{self.window_height}+{x_position}+{y_position}")
        self.font = f"{{TkDefaultFont}} {16} bold"  # Font for text display on image

        self.image_display = tk.Frame(self)
        self.image_display.pack(side=tk.LEFT, expand=True)
        self.control_panel = tk.Frame(self)
        self.control_panel.pack(side=tk.RIGHT, expand=True)

        # Create a button to open another video file
        open_button = tk.Button(self.control_panel, text="Select An Image File", command=self.open_file)
        open_button.pack(padx=10, pady=10)
        self.label = tk.Label(self.control_panel)
        self.label.pack(pady=10)

        self.cal_flag = False  # Track calibration identifier
        self.horz_flag = False  # Track horizontal identifier

        # Create buttons for functions 
        self.delete_points_button = tk.Button(self.control_panel, text="Delete Point", command=self.delete_point)
        self.accept_points_button = tk.Button(self.control_panel, state=tk.DISABLED)
        self.re_cal_button = tk.Button(self.control_panel, text="Re-Calibrate", command=self.calibration)
        self.re_horz_button = tk.Button(self.control_panel, text="Re-Draw Horizontal", command=self.draw_horizontal)
        self.entry = tk.Entry(self.control_panel)
        self.points = []

    def open_file(self):
        try:
            self.file = filedialog.askopenfilename(title="Select an image file", filetypes=[("JPG files", "*.jpg")])
            if self.file:
                if hasattr(self, 'canvas'):
                    self.canvas.destroy()  # Delete the previous canvas if it exists
                    self.image_label.pack_forget()
                self.file_path, ext = os.path.splitext(self.file)
                self.folder_path, self.image_lot = os.path.split(self.file_path)  # Isolate the folder path
                # Create a new canvas and display the selected image
                self.image = Image.open(self.file)
                self.resize_image()
                self.canvas = tk.Canvas(self.image_display, width=self.image_width, height=self.image_height)
                self.canvas.pack(side=tk.TOP, padx=10, fill=tk.BOTH, expand=True)
                self.offset_x = self.image_width / 2
                self.offset_y = self.image_height / 2
                self.image_x = 0
                self.image_y = 0
                self.tk_img = ImageTk.PhotoImage(self.image)
                self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_img)
                self.setup_zoom()  # set up the zoom function
                # Add the lot to the image display
                self.image_label = tk.Label(self.image_display, text=self.image_lot, font=self.font)
                self.image_label.pack(pady=10)
                # Decide which routine to initialize
                if not self.cal_flag:
                    self.calibration()
                elif not self.horz_flag:
                    self.draw_horizontal()
                else:
                    self.measure_droop()
                # Bind a click event to the canvas
                self.canvas.bind("<Button-1>", self.add_point)
        except FileNotFoundError:
            messagebox.showerror("File not found", "The selected file was not found.")

    # Link zoom function to the canvas 
    def setup_zoom(self):
        # Zoom while the "Ctrl" key is depressed with the scroll wheel
        self.bind_all("<KeyPress-Control_L>", self.start_zoom)
        self.bind_all("<KeyRelease-Control_L>", self.reset_cursor)
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.zoom_mode = False

    def resize_image(self):
        target_size = (int(self.window_width * 2 / 3), int(self.window_height * 2 / 3))
        self.image.thumbnail(target_size, Image.Resampling.LANCZOS)
        self.image_width, self.image_height = self.image.size

    # Start the zoom event cascade 
    def start_zoom(self, event):
        self.zoom_mode = True
        self.canvas.config(cursor="plus")

    # Zoom in or out depending on the scroll direction
    def zoom(self, event):
        if event.delta > 0:
            self.zoom_in(event.x, event.y)
        elif event.delta < 0:
            self.zoom_out(event.x, event.y)

    # End the zoom event and restart point selection
    def reset_cursor(self, event):
        self.zoom_mode = False
        self.canvas.config(cursor="")

    def zoom_in(self, x, y):
        if not self.zoom_mode:
            return
        if self.zoom_factor >= 6.0: return  # Cap zoom at 6.0X
        # Zoom in by a factor of 2.0
        zoom_factor = 2.0
        self.zoom_factor *= zoom_factor
        width = int(self.image.width * self.zoom_factor)
        height = int(self.image.height * self.zoom_factor)

        # Get the mouse coordinates
        x = self.canvas.canvasx(x)
        y = self.canvas.canvasy(y)
        cx = self.canvas.winfo_width() / 2
        cy = self.canvas.winfo_height() / 2

        # Adjust the current offset based on the previous offset, mouse selected center
        # point and zoom factor
        self.offset_x = self.offset_x + int(cx - x) * self.zoom_factor / zoom_factor
        self.offset_y = self.offset_y + int(cy - y) * self.zoom_factor / zoom_factor
        # Store the upper left coordinates for the image separately from the image center
        self.image_x = self.offset_x - (width / 2)
        self.image_y = self.offset_y - (height / 2)
        # Ensure the image remains within the canvas boundaries
        if self.offset_x > width - self.canvas.winfo_width():
            self.offset_x = 0
        elif self.offset_x < self.canvas.winfo_width() - width:
            self.offset_x = self.canvas.winfo_width() - width
        if self.offset_y > height - self.canvas.winfo_height():
            self.offset_y = height - self.canvas.winfo_height()
        elif self.offset_y < self.canvas.winfo_height() - height:
            self.offset_y = self.canvas.winfo_height() - height

        # Apply the resizing to the image
        resized_image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_image)
        self.scale_points()

    def zoom_out(self, x, y):
        if not self.zoom_mode:
            return
        self.zoom_factor = 1.0  # Zoom back to original image size
        width = int(self.image.width * self.zoom_factor)
        height = int(self.image.height * self.zoom_factor)
        self.offset_x = width / 2
        self.offset_y = height / 2
        self.image_x = 0
        self.image_y = 0
        # Resize the image with the factored width and height
        resized_image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(resized_image)
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_image)
        self.scale_points()  # Rescale the points and redraw onto the new image scale

    def update_image(self):
        width = int(self.image_width * self.zoom_factor)
        height = int(self.image_height * self.zoom_factor)
        self.offset_x = self.offset_x * (width / self.image_width)
        self.offset_y = self.offset_y * (height / self.image_height)
        self.image_width, self.image_height = width, height
        self.image = self.image.resize((width, height), Image.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_img)

    # Given two points from the canvas coordinate system, convert them into the image coordinate system
    def convert_to_image(self, x, y):
        image_x = (x - self.image_x) / self.zoom_factor  # Distance from upper left corner
        image_y = (y - self.image_y) / self.zoom_factor  # Distance from upper left corner
        return image_x, image_y

    # Given two points from the image coordinate system, convert them into the canvas coordinate system
    def convert_to_canvas(self, x, y):
        canvas_x = x * self.zoom_factor + self.image_x
        canvas_y = y * self.zoom_factor + self.image_y
        return canvas_x, canvas_y

    # Set up the canvas for calibration
    def calibration(self):
        # Reset the control panel
        self.accept_points_button.pack_forget()
        self.delete_points_button.pack_forget()
        self.re_cal_button.pack_forget()
        self.re_horz_button.pack_forget()
        # Reset the calibration flag
        self.cal_flag = False
        # Clear the canvas 
        self.canvas.delete("oval", "overlay")
        # Create an entry box to take in the value of the feature in mm for calibration
        self.label.config(text="Enter Calibration Value (mm)", relief="flat")
        self.entry.pack(pady=10)
        # Add calibration buttons
        self.delete_points_button.pack(pady=10)
        self.accept_points_button.config(text="Accept Calibration", command=self.end_calibration)
        self.accept_points_button.pack(pady=10)
        self.points = []  # Reset the points
        self.scale_points()  # Draw overlays

    # Set up for the horizontal line selection routine
    def draw_horizontal(self):
        # Reset the control panel
        self.re_horz_button.pack_forget()
        self.accept_points_button.config(text="Accept Horizontal", command=self.end_horizontal, state=tk.DISABLED)
        self.label.config(text="Select points to identify the Horizontal Coordinate System", bg="white", relief="solid")
        self.horz_flag = False  # Reset the horizontal line flag
        # Clear the canvas 
        self.canvas.delete("oval", "overlay")
        self.points = []  # Reset the points
        self.scale_points()  # Draw overlays

    # Select points and add to the calibration_points list
    def add_point(self, event):
        # Add clicked points to the calibration points list
        if self.cal_flag and self.horz_flag and len(self.points) == 1:
            return  # Only allow for one point to be selected for measurement
        x, y = event.x, event.y
        image_x, image_y = self.convert_to_image(x, y)
        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red", tags="oval")
        self.points.append((image_x, image_y))
        if len(self.points) >= 2: self.accept_points_button.config(
            state=tk.NORMAL)  # Accept points or lines if 2 or more selected
        if not self.cal_flag or not self.horz_flag:
            self.draw_fitted_line()  # Draw fitted line during calibration
        if self.cal_flag and self.horz_flag:
            self.accept_points_button.config(state=tk.NORMAL)
            self.distance_to_line()  # Display the distance
        self.scale_points()

    # Delete the most recently selected point from cal points
    def delete_point(self):
        if self.points:  # Check if there are points in the array
            self.points.pop()  # Remove the last point from the points list
            self.scale_points()  # Redraw the points to the scale
            # Disable selection if there are not enough points
            if self.horz_flag and len(self.points) < 1:
                return self.accept_points_button.config(state=tk.DISABLED)
            elif len(self.points) < 2:
                self.accept_points_button.config(state=tk.DISABLED)

    # Scale the points shown on the canvas according to the zoom value
    def scale_points(self):
        # Clear the canvas and redraw the points
        self.canvas.delete("oval", "overlay")
        # Draw the applicable lines
        if self.cal_flag:
            x1, y1, x2, y2 = self.calibration_line
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="overlay")  # Draw the line
            text_x, text_y = self.place_text_along_line(x1, y1, x2, y2)  # Calculate the xy for text
            self.canvas.create_text(text_x, text_y, text=(self.entry.get() + " mm"), fill="green", font=self.font,
                                    tags="overlay")  # Define the length
        if self.horz_flag:
            x1, y1, x2, y2 = self.horizontal_line
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="overlay")  # Draw the line
        if not self.points: return
        for point in self.points:
            canvas_x, canvas_y = self.convert_to_canvas(point[0], point[1])
            # Redraw the points into the current canvas view
            if 0 < canvas_x < self.canvas.winfo_width() and 0 < canvas_y < self.canvas.winfo_height():
                self.canvas.create_oval(canvas_x - 3, canvas_y - 3, canvas_x + 3, canvas_y + 3, fill="red", tags="oval")
        if self.cal_flag and self.horz_flag:
            self.draw_distance()
        if not self.cal_flag or not self.horz_flag: self.draw_fitted_line()  # Draw fitted line during calibration

    # Fit a line to a list of points using Linear Regression Model and LSR to optimize the line
    def fit_line(self):
        if len(self.points) < 2:
            return None  # You need at least 2 points to fit a line

        # Linear regression to fit a line (y = mx + b)
        X = np.array([x for x, _ in self.points])
        Y = np.array([y for _, y in self.points])
        A = np.vstack([X, np.ones(len(X))]).T
        m, b = np.linalg.lstsq(A, Y, rcond=None)[0]
        return m, b  # Returns slope and y-int of the fitted line

    # Defines the fitted line in terms of coordinates
    def define_line(self):
        m, b = self.fit_line()
        x1, y1 = min(self.points, key=lambda p: p[0])
        x2, y2 = max(self.points, key=lambda p: p[0])
        y1_line = m * x1 + b
        y2_line = m * x2 + b
        return x1, y1_line, x2, y2_line  # Return the two points used to construct the line

    # Draw the line fit through points
    def draw_fitted_line(self):
        self.canvas.delete("overlay")  # Clear the existing circle overlay
        if len(self.points) >= 2:
            x1, y1, x2, y2 = self.define_line()  # Run the routine to estimate the line through the points
            # Convert the line parameters to the current zoom factor and draw to the canvas
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2, tags="overlay")  # Draw the line
            text_x, text_y = self.place_text_along_line(x1, y1, x2, y2)  # Calculate the xy for text
            if not self.cal_flag: self.canvas.create_text(text_x, text_y, text=(self.entry.get() + " mm"), fill="red",
                                                          font=self.font, tags="overlay")  # Define the length
        if self.cal_flag:
            x1, y1, x2, y2 = self.calibration_line
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="overlay")  # Draw the line
            text_x, text_y = self.place_text_along_line(x1, y1, x2, y2)  # Calculate the xy for text
            self.canvas.create_text(text_x, text_y, text=(self.entry.get() + " mm"), fill="green", font=self.font,
                                    tags="overlay")  # Define the length
        if self.horz_flag:
            x1, y1, x2, y2 = self.horizontal_line
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="overlay")  # Draw the line

    # Calculate the x and y to place text along a line using the bisecting line as reference
    def place_text_along_line(self, x1, y1, x2, y2, distance=10):
        # Calculate the midpoint of the line
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        # Calculate the angle of the line and find the bisecting line angle
        angle = math.atan2(y2 - y1, x2 - x1)
        angle_bisector = angle + math.pi / 2

        # Calculate the new coordinates for placing text above the line
        text_x = mid_x - distance * math.cos(angle_bisector)
        text_y = mid_y - distance * math.sin(angle_bisector)

        return text_x, text_y  # Returns the x and y coordinates for the text

    # Run the saving steps for the calibration routine and run point selection next
    def end_calibration(self):
        self.points_to_value()
        self.calibration_line = (self.define_line())  # Save line used for calibration
        self.cal_flag = True  # Mark that calibration was completed
        self.re_cal_button.pack(pady=10)  # Allow the user to re calibrate if required
        self.entry.pack_forget()
        # Reset the canvas for point selection
        if self.horz_flag:
            self.re_horz_button.pack(pady=10)
            self.measure_droop()  # Set up for the measurement process
        else:
            self.draw_horizontal()  # Set up for the horizontal line selection

    # Take in the calibration points and convert to a pixel/mm value
    def points_to_value(self):
        try:
            float_value = float(self.entry.get())
            x1, y1_line, x2, y2_line = self.define_line()
            distance = math.sqrt((x2 - x1) ** 2 + (y2_line - y1_line) ** 2)
            self.cal_value = distance / float_value
            # self.save_cal_to_xlsx()
        except (ValueError, TypeError):
            return False

    '''    
    # Save the calibration file to the folder path
    def save_cal_to_xlsx(self):
        # Get the current date and time
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("_%Y-%m-%d_%H-%M-%S")
        self.folder_path, image_file = os.path.splitext(self.file)
        excel_file = self.folder_path + formatted_datetime + "_calPoints.xlsx" # Get the file name without an extension
        # Save the calibration points selected and the image identifier to the folder
        data = {'Calibration Points': self.points}
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)
    '''

    # Clear the canvas functionality meant for horizontal coordinate system identification
    def end_horizontal(self):
        self.horizontal_line = self.define_line()  # Save horizontal line coordinates
        self.horz_flag = True  # Mark that horizontal coordinate search was completed
        self.re_horz_button.pack(pady=10)  # Allow for updated horizontal line
        self.measure_droop()  # Set up for droop measurement

    # Setup for measurment routine to occur on material horizontal droop length
    def measure_droop(self):
        self.accept_points_button.config(text="Accept Measurement and Save", command=self.end_measurement,
                                         state=tk.DISABLED)
        self.label.config(text="Select point at the bottom of the material to measure the horizontal drop")
        # Clear the canvas 
        self.canvas.delete("oval")
        self.points = []  # Reset the points
        self.scale_points()  # Draw overlays

    # Calculate the horizontal distance from a point (x, y) to a line defined by two points (x1, y1) and (x2, y2)
    def distance_to_line(self):
        x, y = self.points[0]
        x1, y1, x2, y2 = self.horizontal_line
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        distance = abs(A * x + B * y + C) / ((A ** 2 + B ** 2) ** 0.5)

        # Calculate the coordinates for the line
        self.intersection_x = (B * (B * x - A * y) - A * C) / (A ** 2 + B ** 2)
        self.intersection_y = (A * (-B * x + A * y) - B * C) / (A ** 2 + B ** 2)

        self.distance = distance / self.cal_value
        self.draw_distance()

    # Draw the intersection to the canvas
    def draw_distance(self):
        x, y = self.points[0]
        x, y = self.convert_to_canvas(x, y)
        x1, y1, x2, y2 = self.horizontal_line
        x1, y1 = self.convert_to_canvas(x1, y1)
        x2, y2 = self.convert_to_canvas(x2, y2)
        canvas_x, canvas_y = self.convert_to_canvas(self.intersection_x, self.intersection_y)
        # Draw the dashed lines
        self.extended_line = self.canvas.create_line(canvas_x, canvas_y, x1, y1, fill="red", dash=(4, 4),
                                                     tags="overlay")
        self.distance_line = self.canvas.create_line(x, y, canvas_x, canvas_y, fill="red", dash=(4, 4), tags="overlay")
        # Assuming canvas is your Tkinter Canvas object
        self.canvas.create_text(10, 10, anchor="nw", text=f"Distance: {self.distance:.2f}", fill="red", font=self.font,
                                tags="overlay")

    def save_canvas_to_jpeg(self):
        # Convert the image to RGB mode
        if self.image.mode != 'RGB':
            self.image = self.image.convert('RGB')
        draw = ImageDraw.Draw(self.image)

        # Get the current date and time
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("_%Y-%m-%d_%H-%M-%S")
        file_path, ext = os.path.splitext(self.file)
        folder_path, image_lot = os.path.split(file_path)  # Isolate the folder and the image lot identifier

        # Add an image label to the output image
        font = ImageFont.truetype("arial.ttf", size=16)
        bbox = draw.textbbox((10, 10), image_lot, font=font)
        draw.rectangle((bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2), fill="white", outline="black", width=1)
        draw.text((10, 10), image_lot, font=font, fill="black")

        # Draw the calibration line and calibration value
        x1, y1, x2, y2 = self.calibration_line
        draw.line((x1, y1, x2, y2), fill="green", width=3)
        text_x, text_y = self.place_text_along_line(x1, y1, x2, y2, distance=24)
        bbox = draw.textbbox((text_x, text_y), text=(self.entry.get() + " mm"), font=font)
        draw.rectangle((bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2), fill="white", outline="black", width=1)
        draw.text((text_x, text_y), text=(self.entry.get() + " mm"), font=font, fill="green")

        # Draw the horizontal line
        x1, y1, x2, y2 = self.horizontal_line
        draw.line((x1, y1, x2, y2), fill="green", width=3)
        # Draw the selected point and corresponding distance lines
        x, y = self.points[0]
        draw.line((self.intersection_x, self.intersection_y, x1, y1), fill="blue", width=3)
        draw.line((x, y, self.intersection_x, self.intersection_y), fill="blue", width=3)
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill="red")
        text_x, text_y = self.place_text_along_line(x, y, self.intersection_x,
                                                    self.intersection_y)  # Calculate the xy for text
        bbox = draw.textbbox((text_x - 70, text_y - 20), text=f"{self.distance:.2f} mm", font=font)
        draw.rectangle((bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2), fill="white", outline="black", width=1)
        draw.text((text_x - 70, text_y - 20), text=f"{self.distance:.2f} mm", font=font, fill="red")
        bbox = draw.textbbox((10, 40), text=f"Horizontal Droop (mm): {self.distance:.2f}", font=font)
        draw.rectangle((bbox[0] - 2, bbox[1] - 2, bbox[2] + 2, bbox[3] + 2), fill="white", outline="black", width=1)
        draw.text((10, 40), text=f"Horizontal Droop (mm): {self.distance:.2f}", font=font, fill="red")

        # Save the image to a JPEG file located in the video path
        output_path = file_path + formatted_datetime + "_M.png"  # Save to the working directory
        self.image.save(output_path, format="PNG")

    # Append the material droop measurements to the excel output file
    def append_row_to_excel(self, file_path, headers):
        try:
            # Load the Excel file into a DataFrame
            df = pd.read_excel(file_path)
            lot, subject, _ = self.image_lot.split("_")
            data = [[lot, subject, self.distance]]
            df = pd.concat([df, pd.DataFrame(data, columns=headers)], ignore_index=True)

            # Write the updated DataFrame back to the Excel file
            df.to_excel(file_path, index=False)
        except Exception as e:
            print(f"Error: {e}")

    # Either identify the file used to save the outputted material droop measurements or create it
    def find_or_create_file(self):
        folder, lot = os.path.split(self.folder_path)
        file_name = lot + "_Droop_Measurements.xlsx"
        headers = ["Lot #", "Subject", "Droop Length (mm)"]
        file_path = os.path.join(self.folder_path, file_name)
        if os.path.exists(file_path):
            return file_path, headers
        else:
            # Create the Excel file with specified headers
            df = pd.DataFrame(columns=headers)
            df.to_excel(file_path, index=False)
        return file_path, headers

    # Run saving routine for measurement after point is accepted
    def end_measurement(self):
        self.distance_to_line()
        file_path, headers = self.find_or_create_file()
        self.save_canvas_to_jpeg()
        self.append_row_to_excel(file_path, headers)
        self.open_file()


app = MaterialMeasurement()
app.mainloop()
