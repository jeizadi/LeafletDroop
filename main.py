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
from PIL import Image, ImageTk

class LeafletMeasurement(tk.Tk):
    def __init__(self):    
        super().__init__()
        self.title("Leaflet Measurement Window")
        # Calculate a reasonable size and position for the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.window_width = int(0.8 * screen_width)
        self.window_height = int(0.8 * screen_height)
        x_position = (screen_width - self.window_width) // 2
        y_position = (screen_height - self.window_height) // 2
        # Set the window size and position
        self.geometry(f"{self.window_width}x{self.window_height}+{x_position}+{y_position}")
        self.font = f"{{TkDefaultFont}} {16} bold" # Font for text display on image

        self.image_display = tk.Frame(self)
        self.image_display.pack(side=tk.LEFT, expand=True)
        self.control_panel = tk.Frame(self)
        self.control_panel.pack(side=tk.RIGHT, expand=True)
        
        # Create a button to open another video file
        open_button = tk.Button(self.control_panel, text="Select An Image File", command=self.open_file)
        open_button.pack(padx=10, pady=10) 
        self.label=tk.Label(self.control_panel)
        self.label.pack(pady=10)
        
        self.cal_flag = False # Track calibration identifier
        self.horz_flag = False # Track horizontal identifer
        # Create buttons for functions 
        self.delete_points_button = tk.Button(self.control_panel, text="Delete Point", command=self.delete_point)
        self.accept_points_button = tk.Button(self.control_panel, state=tk.DISABLED)
        self.re_cal_button = tk.Button(self.control_panel, text="Re-Calibrate", command=self.calibration)
        self.points = []

    def open_file(self):
        try:
            self.file = filedialog.askopenfilename(title="Select an image file", filetypes=[("JPG files", "*.jpg")])
            if self.file:
                if hasattr(self, 'canvas'):
                    self.canvas.destroy()  # Delete the previous canvas if it exists
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
                self.setup_zoom() # set up the zoom function
                # Run calibration routine if no cal value is found
                if self.cal_flag: 
                    self.accept_points_button.config(command=self.end_horizontal)
                    self.label.config(text="Select points to identify horizontal coordinate system", bg="white", bd=1, relief="solid")
                    self.accept_points_button.config(text="Accept Horizontal Coordinate System", command=self.end_horizontal)
                else:
                    self.calibration() # Run calibration routine   
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
        self.zoom_factor = 1.0
        self.zoom_mode = False
        
    def resize_image(self):
        target_size = (int(self.window_width*2/3), int(self.window_height*2/3))
        self.image.thumbnail(target_size, Image.Resampling.LANCZOS)
        self.image_width, self.image_height = self.image.size
        
    # Start the zoom event casade 
    def start_zoom(self, event):
        self.zoom_mode = True
        self.canvas.config(cursor="plus")
    
    # Zoom in or out depending on the scroll direction
    def zoom(self, event):
        if (event.delta > 0): self.zoom_in(event.x, event.y)
        elif (event.delta < 0): self.zoom_out(event.x, event.y)
    
    # End the zoom event and restart point selection
    def reset_cursor(self, event):
        self.zoom_mode = False
        self.canvas.config(cursor="")
    
    def zoom_in(self, x, y):
        if not self.zoom_mode:
            return
        if self.zoom_factor >= 6.0: return # Cap zoom at 6.0X
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
        # Store the upper left coordinates for the image seperately from the image center
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
        self.zoom_factor = 1.0 # Zoom back to original image size
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
        self.scale_points() # Rescale the points and redraw onto the new image scale

    def update_image(self):
        width = int(self.image_width * self.zoom_factor)
        height = int(self.image_height * self.zoom_factor)
        self.offset_x = self.offset_x * (width / self.image_width)
        self.offset_y = self.offset_y * (height / self.image_height)
        self.image_width, self.image_height = width, height
        self.image = self.image.resize((width, height), Image.ANTIALIAS)
        self.tk_img = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(self.offset_x, self.offset_y, anchor=tk.CENTER, image=self.tk_img)
        
    # Given two points from the canvas coordinate system, convert them into the image coordinate system
    def convert_to_image(self, x, y):
        image_x = (x - self.image_x) / self.zoom_factor # Distance from upper left corner
        image_y = (y - self.image_y) / self.zoom_factor # Distance from upper left corner
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
        # Reset the calibration flag
        self.cal_flag = False
        self.horz_flag = False
        # Clear the canvas 
        self.canvas.delete("oval", "overlay") 
        # Create an entry box to take in the value of the feature in mm for calibration
        self.label.config(text="Enter Calibration Value (mm)", bg=None, relief="flat")
        self.entry = tk.Entry(self.control_panel)
        self.entry.pack(pady=10)
        
        # Add calibration buttons
        self.delete_points_button.pack(pady=10)
        self.accept_points_button.config(text="Accept Calibration", command=self.end_calibration)
        self.accept_points_button.pack(pady=10)     
        self.points = []

    # Select points and add to the calibration_points list
    def add_point(self, event):
        # Add clicked points to the calibration points list
        if self.horz_flag and len(self.points) == 1: return # Only allow for one point to be selected 
        x, y = event.x, event.y
        image_x, image_y = self.convert_to_image(x, y)
        self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="red", tags="oval")
        self.points.append((image_x, image_y))
        if not self.cal_flag or not self.horz_flag: self.draw_fitted_line() # Draw fitted line during calibration
        if self.horz_flag or len(self.points) >= 2: self.accept_points_button.config(state=tk.NORMAL)
        if self.horz_flag: self.distance_to_line() # Display the distance 
        
    # Delete the most recently selected point from cal points
    def delete_point(self):
        if self.points: # Check if there are points in the array
            self.points.pop() # Remove the last point from the points list
            # Disable selection if there are not enough points
            if self.horz_flag and len(self.points) < 1: return self.accept_points_button.config(state=tk.DISABLED)
            elif len(self.points) < 2: self.accept_points_button.config(state=tk.DISABLED)
            self.scale_points() # Redraw the points to the scale
    
    # Scale the points shown on the canvas according to the zoom value
    def scale_points(self):
        # Clear the canvas and redraw the points
        self.canvas.delete("oval", "overlay") 
        if self.horz_flag: 
            x1, y1, x2, y2 = self.horizontal_line
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="green", width=2, tags="overlay") # Draw the line
        if not self.points: return
        for point in self.points:
            canvas_x, canvas_y = self.convert_to_canvas(point[0], point[1])
            # Redraw the points into the current canvas view
            if 0 < canvas_x < self.canvas.winfo_width() and 0 < canvas_y < self.canvas.winfo_height():
                self.canvas.create_oval(canvas_x - 3, canvas_y - 3, canvas_x + 3, canvas_y + 3, fill="red", tags="oval")
        if not self.cal_flag or not self.horz_flag: self.draw_fitted_line() # Draw fitted line during calibration

    # Fit a line to a list of points using Linear Regression Model and LSR to optimize the line
    def fit_line(self):
        if len(self.points) < 2:
            return None  # You need at least 2 points to fit a line
            
        # Linear regression to fit a line (y = mx + b)
        X = np.array([x for x, _ in self.points])
        Y = np.array([y for _, y in self.points])
        A = np.vstack([X, np.ones(len(X))]).T
        m, b = np.linalg.lstsq(A, Y, rcond=None)[0]
        return m, b # Returns slope and y-int of the fitted line
    
    # Defines the fitted line in terms of coordinates
    def define_line(self):
        m, b = self.fit_line()
        x1, y1 = min(self.points, key=lambda p: p[0])
        x2, y2 = max(self.points, key=lambda p: p[0])
        y1_line = m * x1 + b
        y2_line = m * x2 + b
        return x1, y1_line, x2, y2_line # Return the two points used to construct the line
    
    # Draw the line fit through points
    def draw_fitted_line(self):
        self.canvas.delete("overlay") # Clear the existing circle overlay
        if len(self.points) >= 2:
            x1, y1, x2, y2 = self.define_line() # Run the routine to estimate the line through the points
            # Convert the line parameters to the current zoom factor and draw to the canvas
            x1, y1 = self.convert_to_canvas(x1, y1)
            x2, y2 = self.convert_to_canvas(x2, y2)
            self.canvas.create_line(x1, y1, x2, y2, fill="red", width=2, tags="overlay") # Draw the line
            text_x, text_y = self.place_text_along_line(x1, y1, x2, y2) # Calculate the xy for text
            if not self.cal_flag: self.canvas.create_text(text_x, text_y, text=(self.entry.get() + " mm"), fill="red", font=self.font, tags="overlay") # Define the length

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
        
        return text_x, text_y # Returns the x and y coordinates for the text
    
    # Run the saving steps for the calibration routine and run point selection next
    def end_calibration(self):
        self.points_to_value()
        self.cal_flag = True # Mark that calibration was completed
        # Reset the canvas for point selection
        self.accept_points_button.config(text="Accept Horizontal", command=self.end_horizontal, state=tk.DISABLED)
        self.label.config(text="Select points to identify the Horizontal Coordinate System", bg="white", relief="solid")
        self.re_cal_button.pack(pady=10) # Allow the user to re calibrate if required   
        self.points = [] # Reset the points
        if self.cal_flag:
            self.entry.destroy()
            # Clear the canvas 
            self.canvas.delete("oval", "overlay") 
            
    # Take in the calibration points and convert to a pixel/mm value
    def points_to_value(self):
        try:
            float_value = float(self.entry.get())
            x1, y1_line, x2, y2_line = self.define_line()
            distance = math.sqrt((x2-x1)**2 + (y2_line-y1_line)**2)
            self.cal_value = distance / float_value
            self.save_cal_to_xlsx()
        except (ValueError, TypeError):
            return False
    
    # Save the calibration file to the folder path
    def save_cal_to_xlsx(self):
        # Get the current date and time
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("_%Y-%m-%d_%H-%M-%S")
        folder_path, image_file = os.path.splitext(self.file)
        excel_file = folder_path + formatted_datetime + "_calPoints.xlsx" # Get the file name without an extension
        # Save the calibration points selected and the image identifier to the folder
        data = {'Calibration Points': self.points}
        df = pd.DataFrame(data)
        df.to_excel(excel_file, index=False)
    
    def end_horizontal(self):
        self.horizontal_line = self.define_line() # Save slope and y int of line
        self.canvas.delete("oval", "overlay") 
        self.canvas.create_line(self.horizontal_line, fill="green", width=2, tags="overlay") # Draw the line
        self.horz_flag = True # Mark that horizontal coordinate search was completed
        # Reset the canvas for point selection
        self.accept_points_button.config(text="Accept Measurement and Save", command=self.end_measurement, state=tk.DISABLED)
        self.label.config(text="Select point at the bottom of the leaflet to measure the horizontal drop")
        self.points = [] # Reset the points
        
    def end_measurement(self):
        self.distance_to_line()
        self.save_canvas_to_jpeg()
        self.open_file()
    
    # Calculate the horizontal distance from a point (x, y) to a line defined by two points (x1, y1) and (x2, y2)
    def distance_to_line(self):
        x, y = self.points[0]
        x1, y1, x2, y2 = self.horizontal_line
        A = y2 - y1
        B = x1 - x2
        C = x2*y1 - x1*y2 
        distance = abs(A*x + B*y + C) / ((A**2 + B**2)**0.5)
        
        # Calculate the coordinates for the line
        intersection_x = (B*(B*x - A*y) - A*C) / (A**2 + B**2)
        intersection_y = (A*(-B*x + A*y) - B*C) / (A**2 + B**2)

        # Draw the dashed lines
        self.extended_line = self.canvas.create_line(intersection_x, intersection_y, x1, y1, fill="red", dash=(4, 4), tags="overlay")
        self.distance_line = self.canvas.create_line(x, y, intersection_x, intersection_y, fill="red", dash=(4, 4), tags="overlay")

        self.distance = distance / self.cal_value
        text = f"Distance: {self.distance:.2f}"
        # Assuming canvas is your Tkinter Canvas object
        self.canvas.create_text(10, 10, anchor="nw", text=text, tags="overlay")
'''
    def save_canvas_to_jpeg(self):
        draw = ImageDraw.Draw(self.image)
        
        # Add an image label to the output image
        text=gv.video_file_name
        font=ImageFont.truetype("arial.ttf", size=20)
        bbox = draw.textbbox((10,10), text, font=font)
        draw.rectangle(bbox, fill="white")
        draw.text((10,10), text, font=font, fill="black")
        
        # Add the overlays to the image depending on which calibration scheme was used
        if self.calibration_scheme.get() == self.cal_ring:
            cx, cy, r = self.fit_circle()
            draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline="blue", width=4) #  Add the circle fit to the image
            text_x, text_y = self.place_text_along_line(cx-r, cy, cx+r, cy, distance=24) # Calculate the coordinates for the text
            draw.line((cx-r, cy, cx+r, cy), fill="red", width=2) # Create a radial line
            draw.text((text_x, text_y), text=(self.entry.get()+"mm"), font=font, fill="red") # Add the diameter to the line
        else:
            x1, x2, y1, y2 = self.define_line()
            draw.line((x1, y1, x2, y2), fill="red", width=4)
            text_x, text_y = self.place_text_along_line(x1, y1, x2, y2, distance=24) # Calculate the coordinates for the text
            draw.text((text_x, text_y), text=(self.entry.get()+"mm"), font=font, fill="red")
        
        # Get the current date and time
        current_datetime = datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        
        file_name_without_extension = os.path.splitext(gv.video_file_name)[0] # Get the file name without an extension
        folder_name = file_name_without_extension + "_" + formatted_datetime
        gv.output_folder_path = os.path.join(gv.video_directory, folder_name)
        os.makedirs(gv.output_folder_path)

        # Save the image to a JPEG file located in the video path
        output_path = os.path.join(gv.output_folder_path, "Calibration.png") # Save to the working directory
        self.image.save(output_path, format="PNG")
        '''
    # Create a function to end the calibration when the user accepts the calibration
    # Function calls the points_to_value method before destroying the window to save current cal value
    # to global var gv.calibration_value   
    def accept_points(self):
        if self.points_to_value() is not False:
            self.save_canvas_to_jpeg()
            self.destroy()

app = LeafletMeasurement()
app.mainloop()
