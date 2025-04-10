# Use the official AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.13

# Set the working directory inside the container
WORKDIR /lambda

# Copy the requirements.txt file into the container
COPY ./requirements.txt .

# Install dependencies into a 'package' directory
RUN mkdir package && pip install -r requirements.txt --target ./package

# Copy the Lambda function code into the 'package' directory
COPY lambda_function.py ./package/

# Create the ZIP file using Python's zipfile module
RUN python -m zipfile -c /tmp/bootstrap.zip package/*

ENTRYPOINT ["cat", "/tmp/bootstrap.zip"]