import logging
import json
import os
import time
import requests
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)
import boto3
from botocore.exceptions import ClientError

from boto3.dynamodb.conditions import Key

# testfile = open("test.jpg", "rb")
# tools.uploadToBucket(testfile.name, testfile, "s3917984bucket")

#

db = boto3.resource('dynamodb')
dbclient = boto3.client('dynamodb')
session = boto3.Session()
# s3 = boto3.resource('s3')
s3client = boto3.client('s3')
s3 = boto3.resource('s3')
errors = []
messages = []
usersDB = db.Table('login')
musicDB = db.Table('music')
subDB = db.Table('subscriptions')

db = session.resource('dynamodb')


# table = db.create_table(
#     TableName='test',
#     KeySchema=[
#         {
#             'AttributeName': 'username',
#             'KeyType': 'HASH'
#         },
#         {
#             'AttributeName': 'last_name',
#             'KeyType': 'RANGE'
#         }
#     ],
#     AttributeDefinitions=[
#         {
#             'AttributeName': 'username',
#             'AttributeType': 'S'
#         },
#         {
#             'AttributeName': 'last_name',
#             'AttributeType': 'S'
#         },
#     ],
#     ProvisionedThroughput={
#         'ReadCapacityUnits': 5,
#         'WriteCapacityUnits': 5
#     }
# )


def create_max_hang_table():
    db.create_table(
        TableName='max_hangs',
        AttributeDefinitions=[
            {
                'AttributeName': 'username',
                'AttributeType': 'S'
            },
        ],
        KeySchema=[
            {
                'AttributeName': 'username',
                'KeyType': 'HASH'
            },
        ],

        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )


def add_data_to_max_hang(username, grade, bodyweight):
    table = db.Table('max_hangs')
    output = table.put_item(
        Item={
            'username': username,
            'weight': grade,
            'grade': bodyweight,
        })
    print(output)



def load_from_json(filepath, table_name):
    table = db.Table(table_name)
    file = open(filepath)
    data = json.loads(file.read())
    for entry in data:
        response = table.put_item(
            TableName=table_name,
            Item={
                'username': entry['username'],
                'grade': entry['grade'],
                'weight': entry['weight'],
            }
        )
        print('Uploaded info for: user ' + entry['username'] + ' - climbing grade:' + str(entry['grade']))


def create_and_populate_max_hangs_table():
    print("creating table for max hangs......")
    create_max_hang_table()
    time.sleep(8)


def check_table_exists(table_name):
    result = False
    musicDB = db.Table('max_hangs')
    if musicDB:
        result = True
    return result


def download_image(image_url, artist_name):
    r = requests.get(image_url, allow_redirects=True)
    filename = 'img/' + artist_name + '.jpg'
    open(filename, 'wb').write(r.content)


def download_images_from_json(json_filepath):
    file = open(json_filepath)
    file = json.loads(file.read())
    for song in file['songs']:
        artist = song['artist']
        img_url = song['img_url']
        artist = artist.replace('.', ' ')
        download_image(img_url, artist)
        print('Downloaded  ' + artist + '.jpg - ' + 'from   ' + img_url)


def upload_images_from_folder(folder_path, bucket_name):
    for filename in os.listdir(folder_path):
        file = open(folder_path + filename, 'rb')
        s3.Bucket(bucket_name).put_object(Key=filename, Body=file.read())
        print('uploaded ' + filename + ' to ' + bucket_name)


def upload_image(file, bucket_name):
    filename = secure_filename(file.filename)
    fileKey = time.strftime("%H:%M:%S") + filename
    s3.Bucket(bucket_name).put_object(Key=fileKey, Body=file.read())
    print('uploaded ' + filename + ' to ' + bucket_name)
    return fileKey


def get_img_url(filename):
    url = s3client.generate_presigned_url('get_object',
                                          Params={
                                              'Bucket': 's3917984',
                                              'Key': filename,
                                          },
                                          ExpiresIn=3600)
    return url


def update_img_urls():
    results = musicDB.scan()
    songs = results['Items']
    artists = []
    for song in songs:
        filename = song['artist']
        filename += ".jpg"
        url = s3client.generate_presigned_url('get_object',
                                              Params={
                                                  'Bucket': 's3917984',
                                                  'Key': filename,
                                              },
                                              ExpiresIn=3600)
        expression = "set img_url =" + url
        response = musicDB.update_item(
            Key={'title': song['title'], 'artist': song['artist']},
            UpdateExpression="set img_url=:i",
            ExpressionAttributeValues={
                ':i': url},
            ReturnValues="UPDATED_NEW")
        print(url)


def delete_max_hang_table():
    response = dbclient.delete_table(
        TableName='max_hangs'
    )


def rem_subscription(email, artist, title):
    response = dbclient.delete_item(
        TableName='subscriptions',
        Key={
            'email': {
                'S': email},
            'artist': {
                'S': artist, },

        }
    )


def put_user_info(email, user_name, password):
    login_table = db.Table('login')
    response = login_table.put_item(
        TableName='login',
        Item={
            'email': email,
            'user_name': user_name,
            'password': password
        }
    )
    # Key={'email': {
    #     'S': email}
    # },
    # UpdateExpression ='set',
    # ExpressionAttributeValues={
    #     'user_name': user_name


def store_studentid_users():
    base_id = 3917984
    base_count = 0
    base_password = "012345"
    p_start = 0
    login_table = db.Table('login')
    for x in range(10):
        passwords = '0123456789890123456789'
        email = 's' + str(base_id) + '@student.rmit.edu.au'
        user_name = 'Kim Walls' + str(base_count)
        password = passwords[p_start:p_start + 6]
        put_user_info(email, user_name, password)
        base_id += 1
        base_count += 1
        p_start += 1


# def store_users():
#     base_id = 3917984
#     base_count = 0
#     base_password = "012345"
#     p_start = 0
#     for x in range(10):
#         passwords = '0123456789890123456789'
#
#         entity = datastore.Entity(key=db.key('user'))
#         entity.update({
#             'id': 's' + str(base_id),
#             'user_name': 'Kim Walls' + str(base_count),
#             'password': passwords[p_start:p_start + 6],
#         })
#         db.put(entity)
#         base_id += 1
#         base_count += 1
#         p_start += 1
#         users = tools.fetch_by_key(db, 'user')

class Movies:
    """Encapsulates an Amazon DynamoDB table of movie data."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.dyn_resource = dyn_resource
        self.table = None


# # Upload a new file
# data = open('test.jpg', 'rb')
# s3.Bucket('s3917984bucket').put_object(Key='test.jpg', Body=data)
# # Print out bucket names
# for bucket in s3.buckets.all():
#     print(bucket.name)

def create_table(self, table_name):
    """
    Creates an Amazon DynamoDB table that can be used to store movie data.
    The table uses the release year of the movie as the partition key and the
    title as the sort key.
    :param table_name: The name of the table to create.
    :return: The newly created table.
    """
    try:
        self.table = self.dyn_resource.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'year', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'title', 'KeyType': 'RANGE'}  # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'year', 'AttributeType': 'N'},
                {'AttributeName': 'title', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10})
        self.table.wait_until_exists()
    except ClientError as err:
        logger.error(
            "Couldn't create table %s. Here's why: %s: %s", table_name,
            err.response['Error']['Code'], err.response['Error']['Message'])
        raise
    else:
        return self.table


def fetch_by_key(db, key: str):
    query = db.query(kind=key)
    values = list(query.fetch())
    return values


def get_posts(db, limit):
    query = db.query(kind='post')
    query.order = ['-timestamp']
    posts = query.fetch(limit=limit)
    return posts


def get_user_posts(db, user_name):
    query = db.query(kind='post')
    query.add_filter("user_name", "=", user_name)
    query.order = ['-timestamp']
    posts = query.fetch()
    return posts


def store_account_info(usersDB, email, username, password, imgKey):
    usersDB.put_item(
        Item={
            'email': email,
            'user_name': username,
            'password': password,
            'profile_img': imgKey
        })


def store_subscription(subDB, email, artist, title, img_url, web_url, year):
    subDB.put_item(
        Item={
            'email': email,
            'artist': artist,
            'title': title,
            'img_url': img_url,
            'web_url': web_url,
            'year': year,
        })
