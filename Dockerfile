# pull official base image
FROM python:3.8.5
RUN apt-get update && apt-get install -y
# set work directory
WORKDIR /usr/src/app
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# copy project
COPY . /usr/src/app/
# copy requirements file
# COPY ./requirements.txt /usr/src/app/requirements.txt
# install dependencies
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt
# Optional to serve FASTAPI through uvicorn
# If you build and run the container from docker-compose you do not need the below 2 lines (expose & cmd) comment them.
# If you build and run the container from docker command leave the below 2 line uncomment
EXPOSE 8000
CMD ["uvicorn", "app.main:app",  "--workers", "1", "--host", "0.0.0.0", "--port", "8000"]