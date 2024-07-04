# Use AWS Lambda Python 3.8 image as the base
FROM public.ecr.aws/lambda/python:3.8

# Install zlib-devel
RUN yum update -y && \
    yum install -y zlib-devel

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Lambda function code
COPY resize-image-lambda-function.py .

# Set the CMD to your Lambda handler
CMD ["resize-image-lambda-function.lambda_handler"]