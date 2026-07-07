# Anime Recommendation System

A Python application that recommends anime based on user preferences through a graphical user interface built with Tkinter.

# Acknowledgments

This project was inspired by the undergraduate thesis "Recommendation Algorithms: A Study Applied to Anime Streaming" by Larissa Moreno Silva, presented to the Department of Statistics at the University of Brasília (UnB) in 2021. The thesis served as the primary academic reference for the recommendation methodology implemented in this application.

Like the original study, this project uses anime metadata obtained from MyAnimeList, stored in CSV format, as the dataset for generating recommendations.

# References
- Silva, L. M. (2021). Recommendation Algorithms: A Study Applied to Anime Streaming. Undergraduate Thesis, Department of Statistics, University of Brasília (UnB). Available at: University of Brasília Digital Library (BDM)
- MyAnimeList. Anime database and community. Available at: https://myanimelist.net/

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

Run the app file:

```bash
python app.py
```

Or on Windows:

```bash
py app.py
```

## Project Structure

```
project/
│
├── app.py
├── ui.py
├── theme.py
├── recommendation_engine.py
├── data_service.py
├── README.md
├── requirements.txt
├── assets/
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