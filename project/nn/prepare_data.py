# -*- coding: utf-8 -*-
import csv
import pickle
import random
import shutil
import subprocess
from optparse import OptionParser

import os
import pandas as pd
import numpy as np

from protocol import NetworkData

test_data_percentage = 5
chunk_size = 50000


def main():
    parser = OptionParser()

    parser.add_option('-f', '--train-path',
                      type='string',
                      help='Path to .csv with train data.')

    opts, _ = parser.parse_args()

    data_path = opts.train_path
    if not data_path:
        parser.error('Path to .csv with train data is not given.')

    print('Chunk size: {}, test data percentage: {}'.format(chunk_size, test_data_percentage), end='\n\n')

    temp_folder = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'temp')
    if os.path.exists(temp_folder):
        print('Temp folder already exists. It was deleted.', end='\n\n')
        shutil.rmtree(temp_folder)

    os.mkdir(temp_folder)

    total_count = line_count(data_path)
    test_count = int((total_count / 100.0) * test_data_percentage)

    # because of our data we need to select three values in a row
    test_count = round(test_count / 3)
    indices_with_step_three = list(range(1, total_count, 3))
    random_indices = np.random.choice(indices_with_step_three, test_count)
    test_rows = []
    for x in random_indices:
        test_rows.append(x)
        test_rows.append(x + 1)
        test_rows.append(x + 2)

    data_rows = list(set([x for x in range(0, total_count)]) - set(test_rows))

    print('Original data size: {}'.format(total_count))
    print('Train data size: {}'.format(len(data_rows)))
    print('Test data size: {}'.format(len(test_rows)), end='\n\n')

    # pandas didn't add correct headers to csv by default
    # so we had to do it manually
    with open(data_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)

    # our test data had to be in separate file
    # we need to skip data rows from original file to extract test data
    print('Saving test.csv...')
    test_file_path = os.path.join(temp_folder, 'test.csv')
    test_data = pd.read_csv(data_path, skiprows=data_rows)
    test_data.to_csv(test_file_path, header=header, index=False)

    # TODO: maybe we don't need to save csv at all
    protocol = NetworkData()
    protocol.parse_new_data(load_data(test_file_path))
    protocol_test_path = os.path.join(temp_folder, 'test.p')
    print('Saving test.p...')
    pickle.dump(protocol, open(protocol_test_path, "wb"))

    # it is important to skip test rows there
    # otherwise we will mix train and test data
    data = pd.read_csv(
        data_path,
        chunksize=chunk_size,
        skiprows=test_rows,
    )
    for i, chunk in enumerate(data):
        file_name = 'chunk_{:03}.csv'.format(i)
        file_path = os.path.join(temp_folder, file_name)
        print('Saving {}...'.format(file_name))
        chunk.to_csv(file_path, header=header, index=False)

        protocol = NetworkData()
        protocol.parse_new_data(load_data(file_path))
        protocol_file_name = 'chunk_{:03}.p'.format(i)
        protocol_file_path = os.path.join(temp_folder, protocol_file_name)
        print('Saving {}...'.format(protocol_file_name))
        pickle.dump(protocol, open(protocol_file_path, "wb"))


def line_count(file):
    return int(subprocess.check_output('wc -l {}'.format(file), shell=True).split()[0])


def load_data(path):
    data = []
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['tenpai_player_waiting']:
                data.append(row)
    return data


if __name__ == '__main__':
    main()