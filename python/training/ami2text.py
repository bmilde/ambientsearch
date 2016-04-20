import xml.etree.ElementTree as ET
import os
import codecs
import logging
import sys
import argparse

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
program = os.path.basename(sys.argv[0])
logger = logging.getLogger(program)

def convert_ami(ami_root_dir, txt_output_dir):
    logger.info('Starting conversion process...')

    for myfile in os.listdir(ami_root_dir):
        if myfile.endswith('.xml'):
            with codecs.open(os.path.join(ami_root_dir, myfile), 'r', encoding='utf-8', errors='replace') as in_file:
                raw = in_file.read()
                tree = ET.fromstring(raw)
                text = ET.tostring(tree, encoding='utf-8', method='text')
                output = u' '.join(text.split())
                filename = os.path.splitext(myfile)[0]
                output_file = os.path.join(txt_output_dir, filename + '.txt')
                with codecs.open(output_file, 'w', encoding='utf-8') as out_file:
                    out_file.write(output)

                logger.info(output_file + ' written')

    logger.info('Conversion done.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-a', '--ami-root-dir', dest='ami_root_dir', help='Ami root directory, corpus is read from this directory', type=str, default = './data/ami_raw/words/')
    parser.add_argument('-t', '--txt-output-dir', dest='txt_output_dir', help='Txt output directory', type=str, default = './data/ami_transcripts/' )

    args = parser.parse_args()

    logger.info('Using ami directory:' + args.ami_root_dir)    
    logger.info('Output text is saved in:' + args.txt_output_dir)

    convert_ami(args.ami_root_dir, args.txt_output_dir)
