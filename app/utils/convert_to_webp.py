import os
import uuid
import boto3
from io import BytesIO

import requests
from PIL import Image


def upload_image_to_s3(app, image_bytes, userid, s3_folder_name, file_extension):
    """
    Verilen resim dosyasını Amazon S3'e yükler.

    :param image_bytes: Yüklenmesi gereken resim dosyasının binary verisi
    :return: Yüklenen dosyanın S3 URL'si
    """
    S3_BUCKET_NAME = app.config['S3_BUCKET_NAME']
    s3_folder = app.config[s3_folder_name]
    aws_access_key = app.config['AWS_ACCESS_KEY_ID']
    aws_secret_key = app.config['AWS_SECRET_ACCESS_KEY']
    print(f"env ler okundu --- s3_folder tipi:{type(s3_folder)} -  {s3_folder}")

    # S3'e erişmek için boto3'ün S3 client'ını oluşturuyoruz
    s3 = boto3.client('s3',
                      aws_access_key_id=aws_access_key,
                      aws_secret_access_key=aws_secret_key)

    # Benzersiz bir dosya adı oluşturuyoruz (UUID kullanarak)
    file_name = f"{userid}-{uuid.uuid4()}.{file_extension}"

    # S3 bucket içine dosyanın tam yolu
    s3_key = os.path.join(s3_folder, file_name)

    try:
        # S3'e dosyayı yüklüyoruz
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=s3_key, Body=image_bytes, ContentType='image/png')

        # Yüklenen dosyanın S3 URL'sini oluşturuyoruz
        s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"

        return s3_url
    except Exception as e:
        raise Exception(f"Error uploading file to S3: {str(e)}")

def download_image(image_url):
    """
    Verilen URL'den görüntüyü indirir ve binary formatında geri döner.
    :param image_url: RunPod'dan gelen görüntünün URL'si
    :return: İndirilen görüntünün binary verisi
    """
    response = requests.get(image_url)
    if response.status_code == 200:
        return BytesIO(response.content)  # Görseli binary formatta döndür
    else:
        raise Exception(f"Failed to download image from {image_url}")
def convert_image_to_webp(image_bytes):
    """
    Görseli WebP formatına dönüştürür.
    :param image_bytes: Orijinal resim dosyasının binary verisi
    :return: WebP formatında resim verisi (binary)
    """
    image = Image.open(image_bytes)  # Görseli aç
    webp_image_io = BytesIO()
    image.save(webp_image_io, format="WEBP", quality=80)  # WebP formatına çevir
    webp_image_io.seek(0)  # Byte stream'in başına geri dön
    return webp_image_io
def process_and_save_image(app, runpod_image_url, userid):
    """
    RunPod'dan gelen görseli indirir, WebP formatına çevirir, S3'e yükler ve veritabanına kaydeder.
    :param app: Flask uygulama objesi
    :param runpod_image_url: RunPod'dan gelen orijinal görselin URL'si
    :param userid: Yükleyen kullanıcının ID'si
    :return: Orijinal ve WebP formatındaki görsel URL'leri
    """
    # RunPod'dan gelen orijinal görseli indir
    original_image_bytes = download_image(runpod_image_url)
    # İndirilen görseli WebP formatına dönüştür
    webp_image_bytes = convert_image_to_webp(original_image_bytes)
    # WebP görseli S3'e yükle
    webp_url = upload_image_to_s3(app, webp_image_bytes, userid, file_extension="webp", s3_folder_name="S3_FOLDER_WEBP_IMAGE")
    # Orijinal URL ve WebP URL'yi döndür
    return webp_url