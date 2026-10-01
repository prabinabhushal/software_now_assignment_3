# HIT137 Group Assignment 3 — Image Tile Puzzle

## Project Overview

This project is a desktop image tile puzzle game developed using **Python**, **Tkinter**, and **OpenCV**.

## Technologies Used

* **Python 3**
* **Tkinter** — used to create the desktop GUI
* **OpenCV (`opencv-python`)** — used for image loading, resizing, cropping, padding, rotation, and flipping
* **NumPy** — used for image and array processing
* **Pillow** — used to convert OpenCV images for display in Tkinter

## Installation

Create a virtual environment:
python -m venv venv

### Windows
venv\Scripts\activate

### macOS / Linux
source venv/bin/activate

Install the required packages:
pip install -r requirements.txt

note: if u don't have installed tikinde than install using 
> sudo apt install python3-tk

## Running the Application
python main.py


## repo Structure

├── main.py                 # Main entry point
├── requirements.txt        # Required Python packages
├── README.md               # Project documentation
├── github_link.txt         # GitHub repository link
│
├── src/
│   ├── __init__.py
│   ├── app.py              # Creates the Tkinter root and starts the app
│   ├── gui.py              # PuzzleGUI and user interface
│   ├── puzzle.py           # PuzzleGame and game logic
│   ├── tile.py             # BaseTile and PuzzleTile classes
│   ├── transformations.py  # Transformation classes
│   └── image_processor.py  # Image processing functions
│
├── assets/
│   └── README.md
│
└── outputs/
    └── README.md

