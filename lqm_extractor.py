from zipfile import ZipFile
import hashlib
import shutil
import os
import sys
import json

USAGE = """
lqm extractor
usage: {} <dir containing lqm fiels> <output dir>
""".format(__file__)

__all__ = ['extract']

processed = {
    'texts': {
        None: True,
    },
    'audios': {
        None: True,
    },
    'images': {
        None: True
    }
}

hashing = hashlib.sha512


def hash_str(string):
    return hashing(string.encode()).hexdigest()


def hash_file(filename):
    h = hashing()
    with open(filename,'rb') as fh:
        chunk = 0
        while chunk != b'':
            chunk = fh.read(1024)
            h.update(chunk)
    return h.hexdigest()


def extract_content(js):
    desc_raw = js.get('MemoObjectList', [{}])[0].get('DescRaw')
    return desc_raw


def read_json(path):
    with open(path) as fh:
        js = json.load(fh)
    return js


def write_content(content):
    jlqm_counter = len(processed['texts'])
    with open(r"{}/{}.txt".format(output_text_dir, jlqm_counter), "w") as fp:
        fp.write(content)


def handle_jlqm(path):
    js = read_json(path)
    content = extract_content(js)
    hash = hash_str(content)
    if not processed['texts'].get(hash):
        write_content(content)
        processed['texts'][hash] = True


def handle_audio(path):
    audios_counter = len(processed['audios'])
    hash = hash_file(path)
    if not processed['audios'].get(hash):
        _, extension = os.path.splitext(path)
        shutil.copyfile(path, '{}/{}{}'.format(output_audios_dir, audios_counter, extension))
        processed['audios'][hash] = True
    

def handle_image(path):
    images_counter = len(processed['images'])
    hash = hash_file(path)
    if not processed['images'].get(hash):
        _, extension = os.path.splitext(path)
        shutil.copyfile(path, '{}/{}{}'.format(output_images_dir, images_counter, extension))
        processed['images'][hash] = True


def process_uncompressed(root):
    for dirName, subdir_list, file_list in os.walk(root):
        if 'memoinfo.jlqm' in file_list:
            handle_jlqm('{}/{}'.format(dirName, 'memoinfo.jlqm'))
        if dirName.endswith('audios'):
            for file_name in file_list:
                handle_audio('{}/{}'.format(dirName, file_name))
        if dirName.endswith('images'):
            for file_name in file_list:
                handle_image('{}/{}'.format(dirName, file_name))


def uncompress(path):
    shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    with ZipFile(path, 'r') as zip:
        zip.extractall(temp_dir)


def run(root):
    it = os.scandir(root)
    for entry in it:
        if entry.is_file() and entry.name.endswith('.lqm'):
            uncompress(entry.path)
            process_uncompressed(temp_dir)
    it.close()


def ensure_dirs(dirs):
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def init(input_dir, output_dir):
    global input_root
    input_root = input_dir

    global output_root
    output_root = output_dir

    global output_text_dir
    output_text_dir = '{}/text/'.format(output_root)

    global output_audios_dir
    output_audios_dir = '{}/audios/'.format(output_root)

    global output_images_dir
    output_images_dir = '{}/images/'.format(output_root)

    global temp_dir
    temp_dir = '{}/temp'.format(output_root)

    ensure_dirs([output_root, output_text_dir, output_audios_dir, output_images_dir, temp_dir])


def extract(input_dir, output_dir):
    init(input_dir, output_dir)
    run(input_root)
    shutil.rmtree(temp_dir)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(USAGE)
        exit(0)
    extract(sys.argv[1], sys.argv[2])
