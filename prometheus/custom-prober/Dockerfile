FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY custom-prober.py custom-prober.py
CMD ["python", "custom_prober.py"]