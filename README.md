# Trustgig

<p align="center">
    <em>A data science project using the Cookiecutter Data Science v2 structure.</em>
</p>

---

## Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for
│                         trustgig and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── trustgig           <- Source code for use in this project.
    │
    ├── __init__.py    <- Makes trustgig a Python module
    │
    ├── config.py      <- Store useful variables and configuration
    │
    ├── dataset.py     <- Scripts to download or generate data
    │
    ├── features.py    <- Code to create features for modeling
    │
    ├── modeling
    │   ├── __init__.py
    │   ├── predict.py <- Code to run model inference with trained models
    │   └── train.py   <- Code to train models
    │
    └── plots.py       <- Code to create visualizations
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- pip

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Trustgig
   ```

2. Create a virtual environment:
   ```bash
   make create_environment
   # or manually:
   python -m venv .venv
   ```

3. Activate the environment:
   ```bash
   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

4. Install dependencies:
   ```bash
   make requirements
   # or manually:
   pip install -r requirements.txt
   ```

### Usage

- **Process data:** `make data`
- **Train model:** `make train`
- **Run linting:** `make lint`
- **Format code:** `make format`
- **Clean compiled files:** `make clean`

---

<p><small>Project based on the <a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">Cookiecutter Data Science</a> project template. #ccds</small></p>