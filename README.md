# Anime Recommendation System

A Python application that recommends anime based on user preferences through a graphical user interface built with Tkinter.

## Requirements

- Python 3.10 or later

## Installation

Clone the repository:

```bash
git clone https://github.com/cassiano-sena/AnimeRecommender.git
cd AnimeRecommender
```

Install the required dependency:

```bash
pip install Pillow
```

Or, if you are using the Python Launcher on Windows:

```bash
py -m pip install Pillow
```

Alternatively, the `requirements.txt` file is included:

```bash
pip install -r requirements.txt
```

## Dependencies

### Python Standard Library

The following modules are included with Python and do **not** require installation:

- tkinter
- statistics
- pathlib
- webbrowser
- math
- csv

### External Library

- Pillow

Install it with:

```bash
pip install Pillow
```

## Running the Application

Run the main file:

```bash
python main.py
```

Or on Windows:

```bash
py main.py
```

## Project Structure

```
project/
│
├── main.py
├── README.md
├── requirements.txt
├── assets/
├── images/
└── data/
```

## Notes

- Keep the project folder structure unchanged so the application can correctly locate images and CSV files.
- If you encounter a `ModuleNotFoundError` related to Pillow, verify the installation by running:

```bash
pip show Pillow
```

## License

This project was developed for educational purposes.