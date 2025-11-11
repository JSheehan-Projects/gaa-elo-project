# GAA ELO Ratings Explorer

A web application for exploring and visualizing the ELO rating history of intercounty GAA teams since 2009.



## 🚀 Live Demo

**(Link to your live Streamlit Cloud app will go here once you deploy it!)**

## Features

* View ELO development for Football and Hurling.
* Compare multiple teams against each other on the same graph.
* Filter by season to see stats like "Biggest Shock Result".
* Fully interactive charts powered by Plotly.

## 🛠️ Tech Stack

* **Python**
* **Streamlit** (Web App)
* **Pandas** (Data Manipulation)
* **Plotly** (Interactive Visualizations)
* **Docker** (Containerization)

## 🏃 How to Run Locally

### 1. With Python (Recommended for development)

```bash
# Clone the repository
git clone [https://github.com/your-username/gaa-elo-project.git](https://github.com/your-username/gaa-elo-project.git)
cd gaa-elo-project

# (Optional but recommended: Create a virtual environment)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### 2. With Docker

```bash
# 1. Build the Docker image
docker build -t gaa-elo-app .

# 2. Run the Docker container
docker run -p 8501:8501 gaa-elo-app
```

Now, open your browser and go to `http://localhost:8501`.