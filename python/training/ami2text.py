import xml.etree.ElementTree as ET
import os
import codecs
import logging
import sys

def data_directory():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

ami_root_dir = os.path.join(data_directory(), 'ami_raw')
txt_output_dir = os.path.join(data_directory(), 'ami_transcripts')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = os.path.basename(sys.argv[0])
logger = logging.getLogger(program)

logger.info('Starting conversion process...')

for file in os.listdir(ami_root_dir):
    if file.endswith('.xml'):
        with codecs.open(os.path.join(ami_root_dir, file), 'r', encoding='utf-8', errors='replace') as in_file:
            raw = in_file.read()
            tree = ET.fromstring(raw)
            text = ET.tostring(tree, encoding='utf-8', method='text')
            output = u' '.join(text.split())
            filename = os.path.splitext(file)[0]
            output_file = os.path.join(txt_output_dir, filename + '.txt')
            with codecs.open(output_file, 'w', encoding='utf-8') as out_file:
                out_file.write(output)

            logger.info(output_file + ' written')


logger.info('Conversion done.')
