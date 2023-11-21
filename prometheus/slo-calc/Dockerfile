FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY slo-calc.py slo-calc.py
CMD ["python", "slo-calc.py"]