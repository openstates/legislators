#!/usr/bin/env python

import os
import glob
import yaml
import click
from utils import get_filename, get_data_dir


class ListDifference:
    def __init__(self, key_name, list_item, which_list):
        self.key_name = key_name
        self.list_item = list_item
        self.which_list = which_list

    def __eq__(self, other):
        return (self.key_name == other.key_name and
                self.list_item == other.list_item and
                self.which_list == other.which_list)


class ItemDifference:
    def __init__(self, key_name, value_one, value_two):
        self.key_name = key_name
        self.value_one = value_one
        self.value_two = value_two

    def __eq__(self, other):
        return (self.key_name == other.key_name and
                self.value_one == other.value_one and
                self.value_two == other.value_two)


def compare_objects(obj1, obj2, prefix=''):
    combined_keys = set(obj1) | set(obj2)
    differences = []
    for key in combined_keys:
        key_name = '.'.join((prefix, key)) if prefix else key
        val1 = obj1.get(key)
        val2 = obj2.get(key)
        if isinstance(val1, list) or isinstance(val2, list):
            # we can compare this way since order doesn't matter
            if val1 is None:
                val1 = []
            if val2 is None:
                val2 = []
            for item in val1:
                if item not in val2:
                    differences.append(ListDifference(key_name, item, 'first'))
            for item in val2:
                if item not in val1:
                    differences.append(ListDifference(key_name, item, 'second'))
        elif isinstance(val1, dict) or isinstance(val2, dict):
            differences.extend(compare_objects(val1 or {}, val2 or {}, prefix=key_name))
        elif val1 != val2:
            differences.append(ItemDifference(key_name, val1, val2))
    return differences


def calculate_similarity(existing, new):
    """
        if everything is equal except for the id: 1
        if names differ, maximum match is 0.8
        for each item that differs, we decrease score by 0.1
    """
    differences = compare_objects(existing, new)

    # if nothing differs or only id differs
    if len(differences) == 0 or (len(differences) == 1 and differences[0].key_name == 'id'):
        return 1

    if existing['name'] != new['name']:
        score = 0.9     # will have another 0.1 deducted later
    else:
        score = 1

    score -= 0.1*len(differences)

    # don't count id difference
    if existing['id'] != new['id']:
        score += 0.1

    if score < 0:
        score = 0

    return score


def directory_merge(existing_people, new_people, threshold=0.7):
    perfect_matches = []
    unmatched = set()
    matched = set()
    perfect_matched = set()

    for new in new_people:
        unmatched.add(new['id'])
        for existing in existing_people:
            similarity = calculate_similarity(existing, new)
            if similarity > 0.99:
                perfect_matched.add(new['id'])
            elif similarity > threshold:
                print('likely match: {} with new {} {}'.format(
                    get_filename(existing), get_filename(new), similarity
                ))
                matched.add(new['id'])

    unmatched -= matched
    unmatched -= perfect_matched
    print('unmatched', unmatched)
    print('perfect_matches', perfect_matches)


def check_merge_candidates(abbr):
    existing_people = []
    for filename in (glob.glob(os.path.join(get_data_dir(abbr), 'people/*.yml')) +
                     glob.glob(os.path.join(get_data_dir(abbr), 'retired/*.yml'))):
        with open(filename) as f:
            existing_people.append(yaml.load(f))

    new_people = []
    incoming_dir = get_data_dir(abbr).replace('test', 'incoming')
    for filename in glob.glob(os.path.join(incoming_dir, 'people/*.yml')):
        with open(filename) as f:
            new_people.append(yaml.load(f))

    print(len(existing_people))
    print(len(new_people))

    directory_merge(existing_people, new_people)


@click.command()
# @click.argument('abbr', default='*')
# @click.option('-v', '--verbose', count=True)
@click.option('--incoming', default=None)
def entrypoint(incoming):
    if incoming:
        check_merge_candidates(incoming)


if __name__ == '__main__':
    entrypoint()