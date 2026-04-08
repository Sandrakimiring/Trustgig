# Trustgig

<p align="center">
    <em>An AI-powered gig worker verification and matching platform combining machine learning with SMS integration.</em>
</p>

---

## Overview

Trustgig is a data science and backend application designed to verify and match gig workers with opportunities. It leverages modern machine learning techniques (sentence transformers, FAISS embeddings) combined with a FastAPI backend to provide intelligent worker-to-opportunity matching. The platform integrates with Africa's Talking for SMS communication and OpenAI for enhanced AI capabilities.

**Tech Stack:**
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL
- **ML/Embeddings:** Sentence Transformers, FAISS, PyTorch, scikit-learn
- **SMS:** Africa's Talking API
- **AI:** OpenAI Integration
- **Frontend:** HTML (39.5% of codebase)
- **Python:** 58.2% of codebase

---

## Features

✨ **Core Capabilities:**
- **Intelligent Matching:** Uses sentence transformers and FAISS to semantically match workers with opportunities
- **Worker Verification:** AI-powered verification system for gig workers
- **SMS Integration:** SMS-based communication via Africa's Talking
- **FastAPI Backend:** High-performance async API for real-time matching
- **Database Support:** PostgreSQL with SQLAlchemy ORM for reliable data persistence
- **ML Pipeline:** Complete pipeline from data processing to model inference
- **AI Enhancement:** OpenAI integration for advanced capabilities

---

## Project Organization

```
├── LICENSE                    <- Open-source license
├── Makefile                   <- Convenience commands (make data, make train, etc.)
├── README.md                  <- Project documentation
│
├── data/                      <- Data directory (organized by processing stage)
│   ├── raw/                   <- Original immutable data
│   ├── interim/               <- Intermediate transformed data
│   ├── processed/             <- Final datasets for modeling
│   └── external/              <- Third-party data
│
├── docs/                      <- MkDocs project for documentation
│
├── models/                    <- Trained models and model artifacts
│
├── reports/                   <- Generated analyses and visualizations
│   └── figures/               <- Generated graphics
│
├── frontend/                  <- HTML frontend components
│
├── backend/                   <- Backend application code
│
├── ai_routes/                 <- AI-specific API routes
│
├── trustgig/                  <- Main Python package
│   ├── __init__.py
│   ├── config.py              <- Configuration and path variables
│   ├── dataset.py             <- Data loading and generation scripts
│   ├── features.py            <- Feature engineering code
│   ├── plots.py               <- Visualization code
│   └── modeling/
│       ├── train.py           <- Model training logic
│       └── predict.py         <- Model inference code
│
├── requirements.txt           <- Python dependencies
├── pyproject.toml             <- Project metadata and tool configuration
├── setup.cfg                  <- Flake8 configuration
│
├── download_model.py          <- Script to download pre-trained models
├── migrate.py                 <- Database migration script
├── seed_data.py               <- Database seeding script
└── test_*.py                  <- Test files for various components
```

---

## Getting Started

### Prerequisites

- **Python:** 3.9 or higher
- **pip:** Package manager
- **Git:** For version control
- **PostgreSQL:** (Optional) For production database

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sandrakimiring/Trustgig.git
   cd Trustgig
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # On Windows
   .venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Download ML models (optional):**
   ```bash
   python download_model.py
   ```

### Quick Start

**Run the development server:**
```bash
uvicorn backend.main:app --reload
```

The API will be available at `http://localhost:8000`

**Data processing:**
```bash
make data
```

**Train models:**
```bash
make train
```

---

## Available Commands

Use the Makefile for common tasks:

```bash
make create_environment    # Create Python virtual environment
make requirements           # Install dependencies
make data                   # Process raw data into datasets
make train                  # Train ML models
make lint                   # Run code linting (flake8)
make format                # Format code with black and isort
make clean                 # Remove compiled Python files
```

---

## Key Dependencies

### Web Framework & API
- `fastapi` - Modern async web framework
- `uvicorn` - ASGI server
- `httpx` - HTTP client

### Database
- `sqlalchemy` - ORM and database toolkit
- `psycopg2-binary` - PostgreSQL adapter
- `asyncpg` - Async PostgreSQL driver

### Machine Learning & Embeddings
- `torch` - Deep learning framework (CPU-only)
- `sentence-transformers` - Semantic text embeddings
- `faiss-cpu` - Similarity search and clustering
- `scikit-learn` - Machine learning utilities
- `numpy`, `pandas` - Data manipulation

### Communication
- `africastalking` - SMS integration
- `requests` - HTTP requests

### AI & Utilities
- `openai` - OpenAI API integration
- `python-dotenv` - Environment variable management
- `click` - CLI framework

For complete dependency list, see `requirements.txt`

---

## Configuration

Create a `.env` file (see `.env.example` for template):

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/trustgig

# Africa's Talking
AFRICASTALKING_USERNAME=your_username
AFRICASTALKING_API_KEY=your_api_key

# OpenAI
OPENAI_API_KEY=your_openai_key

# Application
DEBUG=False
LOG_LEVEL=INFO
```

---

## Development

### Code Quality

The project uses modern Python tooling:
- **black** - Code formatting (line length: 99)
- **flake8** - Linting
- **isort** - Import sorting
- **pytest** - Testing

### Code Style
- Line length: 99 characters
- Python version: 3.9+
- Tools configured in `pyproject.toml` and `setup.cfg`

### Testing

```bash
# Run tests
pytest

# Run specific test file
pytest test_embedder.py

# Test local endpoints
python test_endpoint_local.py
```

---

## Database

### Migrations
```bash
python migrate.py
```

### Seeding Sample Data
```bash
python seed_data.py
```

---

## ML Pipeline

The project includes a complete machine learning pipeline:

1. **Data Processing** (`trustgig/dataset.py`)
   - Loading and cleaning raw data
   - Data validation and transformation

2. **Feature Engineering** (`trustgig/features.py`)
   - Creating features for model training
   - Embedding generation using sentence transformers

3. **Model Training** (`trustgig/modeling/train.py`)
   - Training matching algorithms
   - Model evaluation and validation

4. **Inference** (`trustgig/modeling/predict.py`)
   - Running trained models for worker-opportunity matching
   - Real-time prediction API endpoints

5. **Embeddings** (`test_embedder.py`)
   - Semantic similarity testing
   - FAISS index management

---

## API Endpoints

The FastAPI backend provides RESTful endpoints for:
- Worker profile management
- Opportunity listings
- Semantic matching between workers and opportunities
- SMS communication
- AI-enhanced insights

See `ai_routes/` and `backend/` for endpoint implementations.

---

## Contributing

Contributions are welcome! Please ensure:
1. Code follows the black/isort style guide
2. All tests pass
3. Linting passes (`make lint`)
4. Code is properly formatted (`make format`)

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For questions or issues:
- Open an issue on GitHub
- Check existing documentation in the `docs/` folder
- Review test files for usage examples

---

<p><small>Project based on the <a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">Cookiecutter Data Science</a> project template.</small></p>
```
This comprehensive README includes:
