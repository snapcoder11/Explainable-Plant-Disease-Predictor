# Use the official Python 3.9 image
FROM python:3.9

# Set the working directory to /code
WORKDIR /code

# Copy the current directory contents into the container at /code
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Create necessary directories
RUN mkdir -p /code/outputs/checkpoints

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Change the working directory to the user's home directory
WORKDIR $HOME/app

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user . $HOME/app

# Start the FastAPI application on port 7860 (Hugging Face default)
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "7860"]
