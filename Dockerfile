FROM python:3.11
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN pip install .
ENV GRADIENT_SECRET=4bf18fd77f384485
ENV RACING_API_USERNAME=UR5ogzdYDpq76iOMrKCIQfub
ENV RACING_API_PASSWORD=T5UBuBi5RrYTVJYDqrewft2m
ENV RACING_API_URL=https://api.theracingapi.com/v1
ENV FIREBASE_SECRET=AIzaSyBOiof9vGhH3Pt7aTcSEgy766gc5glqcb8
CMD ["python", "server.py"]
EXPOSE 8080