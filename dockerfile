FROM public.ecr.aws/lambda/python:3.8

# Install zlib development package
RUN yum install -y zlib-devel

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY resize-image-lambda-function.py ./
CMD ["resize-image-lambda-function.lambda_handler"]