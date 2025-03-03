FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
EXPOSE 8001
CMD ["uvicorn", "admin-system:app", "--host", "0.0.0.0", "--port", "8001"]