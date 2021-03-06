import json
from io import BytesIO

import marshmallow
import pytest
import sys

from api import app
from api.error import ErrorCode
from faf import db
from faf.api import ModSchema


@pytest.fixture
def mods(request):
    with db.connection:
        cursor = db.connection.cursor()
        cursor.execute("TRUNCATE TABLE table_mod")
        cursor.execute("""INSERT INTO table_mod
        (uid, name, version, author, ui, date, description, filename, icon, likes, likers) VALUES
        ('mod-1', 'a', '1', 'author1', 0, FROM_UNIXTIME(1), '', 'mod1.zip', '', 100, x'00'),
        ('mod-2', 'b', '2', 'author2', 0, FROM_UNIXTIME(2), '', 'mod2.zip', 'mod2.png', 200, x'00'),
        ('mod-3', 'c', '3', 'author3', 0, FROM_UNIXTIME(3), '', 'mod3.zip', 'mod3.png', 300, x'00')""")

    def finalizer():
        with db.connection:
            cursor = db.connection.cursor()
            cursor.execute("TRUNCATE TABLE table_mod")

    request.addfinalizer(finalizer)


def test_mods(test_client, mods):
    response = test_client.get('/mods')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert 'data' in result
    assert len(result['data']) == 3

    for item in result['data']:
        assert 'type' in item


def test_mods_fields(test_client, mods):
    response = test_client.get('/mods?fields[mod]=name')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert 'data' in result
    assert len(result['data']) == 3
    assert len(result['data'][0]['attributes']) == 1

    for item in result['data']:
        assert 'name' in item['attributes']
        assert 'version' not in item['attributes']


def test_mods_fields_two(test_client, mods):
    response = test_client.get('/mods?fields[mod]=name,author')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert 'data' in result
    assert len(result['data']) == 3
    assert len(result['data'][0]['attributes']) == 2

    for item in result['data']:
        assert 'name' in item['attributes']
        assert 'author' in item['attributes']
        assert 'version' not in item['attributes']


def test_mod(test_client, mods):
    response = test_client.get('/mods/mod-1')
    schema = ModSchema()

    result, errors = schema.loads(response.data.decode('utf-8'))

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'
    assert not errors
    assert result['author'] == 'author1'


def test_mod_not_found(test_client, mods):
    response = test_client.get('/mods/i_do_not_exist')

    assert response.status_code == 404
    assert response.content_type == 'application/vnd.api+json'

    data = json.loads(response.data.decode('utf-8'))

    assert 'errors' in data


def test_mods_page_size(test_client, mods):
    response = test_client.get('/mods?page[size]=1')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert 'data' in result
    assert len(result['data']) == 1


def test_mods_invalid_page_size(test_client, mods):
    response = test_client.get('/mods?page[size]=1001')

    result = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 400
    assert result['errors'][0]['code'] == ErrorCode.QUERY_INVALID_PAGE_SIZE.value['code']
    assert result['errors'][0]['meta']['args'] == [1001]


def test_mods_page(test_client, mods):
    response = test_client.get('/mods?page[size]=1&page[number]=2')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert 'data' in result
    assert len(result['data']) == 1
    assert result['data'][0]['attributes']['name'] == 'b'


def test_mods_invalid_page(test_client, mods):
    response = test_client.get('/mods?page[number]=-1')

    result = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 400
    assert result['errors'][0]['code'] == ErrorCode.QUERY_INVALID_PAGE_NUMBER.value['code']
    assert result['errors'][0]['meta']['args'] == [-1]


def test_mods_download_url(test_client, mods):
    response = test_client.get('/mods?sort=name')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert len(result['data']) > 0

    mod = result['data']
    assert mod[0]['attributes']['download_url'] == 'http://content.faforever.com/faf/vault/mod1.zip'
    assert mod[1]['attributes']['download_url'] == 'http://content.faforever.com/faf/vault/mod2.zip'
    assert mod[2]['attributes']['download_url'] == 'http://content.faforever.com/faf/vault/mod3.zip'


def test_mods_thumbnail_url(test_client, mods):
    response = test_client.get('/mods?sort=name')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert len(result['data']) > 0

    mod = result['data']
    assert 'thumbnail_url' not in mod[0]['attributes']
    assert mod[1]['attributes']['thumbnail_url'] == 'http://content.faforever.com/faf/vault/mods_thumbs/mod2.png'
    assert mod[2]['attributes']['thumbnail_url'] == 'http://content.faforever.com/faf/vault/mods_thumbs/mod3.png'


def test_mods_sort_by_create_time(test_client, mods):
    response = test_client.get('/mods?sort=create_time')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert len(result['data']) > 0

    previous_create_time = marshmallow.utils.from_iso('1970-01-01T00:00:00+00:00')
    for item in result['data']:
        new_date = marshmallow.utils.from_iso(item['attributes']['create_time'])
        assert new_date > previous_create_time
        previous_create_time = new_date


def test_mods_sort_by_likes(test_client, mods):
    response = test_client.get('/mods?sort=likes')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert len(result['data']) > 0

    previous_create_time = -1
    for item in result['data']:
        assert item['attributes']['likes'] > previous_create_time
        previous_create_time = item['attributes']['likes']


def test_mods_sort_by_likes_desc(test_client, mods):
    response = test_client.get('/mods?sort=-likes')

    assert response.status_code == 200
    assert response.content_type == 'application/vnd.api+json'

    result = json.loads(response.data.decode('utf-8'))
    assert len(result['data']) > 0

    previous_likes = sys.maxsize
    for item in result['data']:
        assert item['attributes']['likes'] < previous_likes
        previous_likes = item['attributes']['likes']


def test_mods_inject_sql_order(test_client):
    response = test_client.get("/mods?sort=' or%201=1; --")

    result = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 400
    assert result['errors'][0]['code'] == ErrorCode.QUERY_INVALID_SORT_FIELD.value['code']
    assert result['errors'][0]['meta']['args'] == ["' or 1=1; --"]


def test_mods_upload(test_client, app, tmpdir):
    upload_dir = tmpdir.mkdir("map_upload")
    app.config['MOD_UPLOAD_PATH'] = upload_dir.strpath
    response = test_client.post('/mods/upload',
                                data={'file': (BytesIO('my file contents'.encode('utf-8')), 'mod_name.zip')})

    assert response.status_code == 200
    assert 'ok' == response.get_data(as_text=True)

    with open(upload_dir.join('mod_name.zip').strpath, 'r') as file:
        assert file.read() == 'my file contents'


def test_mods_upload_no_file_results_400(test_client, app, tmpdir):
    response = test_client.post('/mods/upload')

    result = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 400
    assert result['errors'][0]['code'] == ErrorCode.UPLOAD_FILE_MISSING.value['code']


def test_mods_upload_txt_results_400(test_client, app, tmpdir):
    response = test_client.post('/mods/upload', data={'file': (BytesIO('1'.encode('utf-8')), 'mod_name.txt')})

    result = json.loads(response.data.decode('utf-8'))

    assert response.status_code == 400
    assert result['errors'][0]['code'] == ErrorCode.UPLOAD_INVALID_FILE_EXTENSION.value['code']
    assert result['errors'][0]['meta']['args'] == ['zip']
