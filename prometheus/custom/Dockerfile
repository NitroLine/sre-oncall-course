FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY custom_oncall_exporter.py custom_oncall_exporter.py
CMD ["python", "custom_oncall_exporter.py"]