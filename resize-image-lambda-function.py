import os
import boto3
from io import BytesIO
from PIL import Image
import logging
from botocore.exceptions import ClientError
import urllib.parse

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

def get_file_extension(image_format):
    if image_format == 'JPEG':
        return 'jpg'
    elif image_format == 'PNG':
        return 'png'
    else:
        return 'jpg'  # Default to 'jpg' for other formats

def lambda_handler(event, context):
    # Get the source and destination buckets from environment variables
    source_bucket = os.environ['SOURCE_BUCKET']
    destination_bucket = os.environ['DESTINATION_BUCKET']
    logger.info(f"Using source bucket: {source_bucket}")
    logger.info(f"Using destination bucket: {destination_bucket}")

    # Retrieve the object key from the event
    original_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    logger.info(f"Received event for key: {original_key}")
    
    # Get the RESIZED_PREFIX environment variable
    resized_prefix = os.environ.get('RESIZED_PREFIX', 'resized')
    logger.info(f"Using prefix for resized images: {resized_prefix}")

    try:
        # Download the image from S3
        logger.info(f"Downloading image from S3: {source_bucket}/{original_key}")
        try:
            response = s3.get_object(Bucket=source_bucket, Key=original_key)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"Object not found in S3 bucket: {source_bucket}, key: {original_key}")
            elif e.response['Error']['Code'] == 'AccessDenied':
                logger.error(f"Access denied to S3 bucket: {source_bucket}, key: {original_key}")
            else:
                logger.error(f"Error accessing S3 object: {str(e)}")
            raise e

        image_data = response['Body'].read()

        # Open the image using Pillow
        logger.info("Opening image using Pillow")
        image = Image.open(BytesIO(image_data))

        # Define the desired sizes for resizing
        sizes = {
            'thumbnail': (128, 128),
            'medium': (512, 512),
            'large': (1024, 1024)
        }

        # Resize the image and upload to S3 with the configured prefix
        for size_name, size in sizes.items():
            logger.info(f"Resizing image to {size_name} ({size[0]}x{size[1]})")
            resized_image = image.copy()
            resized_image.thumbnail(size)
            buffer = BytesIO()
            resized_image.save(buffer, format=image.format)
            buffer.seek(0)

            # Generate the resized image key with the configured prefix
            file_extension = get_file_extension(image.format)
            resized_key = f"{resized_prefix}/{os.path.splitext(original_key)[0]}_{size_name}.{file_extension}"
            logger.info(f"Uploading resized image to S3: {destination_bucket}/{resized_key}")

            # Upload the resized image to S3
            s3.put_object(
                Bucket=destination_bucket,
                Key=resized_key,
                Body=buffer,
                ContentType=f"image/{file_extension}"
            )

        logger.info("Image resized successfully")
        return {
            'statusCode': 200,
            'body': 'Image resized successfully'
        }

    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error resizing image: {str(e)}"
        }