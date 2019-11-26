FROM python:2.7.17

# Also exposing VSCode debug ports
# EXPOSE 8000 9929 9230


WORKDIR /app
COPY ./requirements*.txt ./
COPY ./setup.* ./
RUN pip install -r requirements.txt
RUN pip install -r requirements_for_test.txt

# COPY . .

# RUN mkdir src
VOLUME /app

ENTRYPOINT ["make", "app_run"]
# CMD ["--", "--port", "8000", "--host", "0.0.0.0"]
