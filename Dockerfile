# 1. Start with an official Python base image
FROM python:3.10-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first for better caching
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all your project files (app.py, data/ folder) into the container
COPY . .

# 6. Expose the port Streamlit runs on (default is 8501)
EXPOSE 8501

# 7. The command to run when the container starts
CMD ["streamlit", "run", "app.py"]