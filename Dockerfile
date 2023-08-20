FROM python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install .
CMD ["python3", "application/scheduler.py"]