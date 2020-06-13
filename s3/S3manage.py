import json
import boto3

class S3:
  def __init__(self, bucket):
    self.bucket = bucket
    self.s3 = boto3.resource('s3').Bucket(self.bucket)

  def upload(self, upload_file):
    try:
      self.s3.upload_file(upload_file, upload_file.split('/')[-1])
      return True
    except:
      return False
  
  def download(self, from_download_file, to_download):
    try:
      self.s3.download_file(from_download_file, to_download)
      return True
    except:
      return False
  
  def get(self):
    return self.s3.name