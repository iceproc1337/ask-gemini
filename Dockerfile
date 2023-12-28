FROM python:3.12-bookworm

# Set the environment variable to tell pipenv to create the virtual environment in the project directory
ENV PIPENV_VENV_IN_PROJECT=1

# Install pipenv for dependency management
RUN pip install pipenv

# Create a directory for the application
RUN mkdir /app

# Set the working directory to the application directory
WORKDIR /app

# Copy the Pipfile and Pipfile.lock to the application directory. As long as this file is not changed, the dependencies will be cached.
COPY ./Pipfile* /app

# Run pipenv sync to update the dependencies
RUN pipenv sync

# Copy all other files to the application directory
COPY ./ /app

# Production server waitress opens port 8080 by default
EXPOSE 8080

# Define our entrypoint command
ENTRYPOINT ["pipenv", "run", "start"]
