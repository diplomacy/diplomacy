# ==============================================================================
# Copyright (C) 2019 - Philip Paquette
#
#  This program is free software: you can redistribute it and/or modify it under
#  the terms of the GNU Affero General Public License as published by the Free
#  Software Foundation, either version 3 of the License, or (at your option) any
#  later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
#  FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
#  details.
#
#  You should have received a copy of the GNU Affero General Public License along
#  with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
""" Convoy paths
    - Contains utilities to generate all the possible convoy paths for a given map
"""
import collections
import hashlib
import glob
import pickle
import multiprocessing
import os
from queue import Queue
import threading
import tqdm
from diplomacy.engine.map import Map
from diplomacy import settings

# Using `os.path.expanduser()` to find home directory in a more cross-platform way.
HOME_DIRECTORY = os.path.expanduser('~')
if HOME_DIRECTORY == '~':
    raise RuntimeError('Cannot find home directory. Unable to save cache')

# Constants
__VERSION__ = '20180307_0955'

# We need to cap convoy length, otherwise the problem gets exponential
SMALL_MAPS = ['standard', 'standard_france_austria', 'standard_germany_italy', 'ancmed', 'colonial', 'modern', 'pure',
              'ancmed_age_of_empires', 'standard_age_of_empires', 'standard_age_of_empires_2', 'standard_fleet_rome']
SMALL_MAPS_CONVOY_LENGTH = 25
ALL_MAPS_CONVOY_LENGTH = 12
CACHE_FILE_NAME = 'convoy_paths_cache.pkl'
DISK_CACHE_PATH = os.path.join(HOME_DIRECTORY, '.cache', 'diplomacy', CACHE_FILE_NAME)

def display_progress_bar(queue, max_loop_iters):
    """ Displays a progress bar
        :param queue: Multiprocessing queue to display the progress bar
        :param max_loop_iters: The expected maximum number of iterations
    """
    progress_bar = tqdm.tqdm(total=max_loop_iters)
    for _ in iter(queue.get, None):
        progress_bar.update()
    progress_bar.close()

def get_convoy_paths(map_object, start_location, max_convoy_length, queue):
    """ Returns a list of possible convoy destinations with the required units to get there
        Does a breadth first search from the starting location

        :param map_object: The instantiated map
        :param start_location: The start location of the unit (e.g. 'LON')
        :param max_convoy_length: The maximum convoy length permitted
        :param queue: Multiprocessing queue to display the progress bar
        :return: A list of ({req. fleets}, {reachable destinations})
        :type map_object: diplomacy.Map
    """
    to_check = Queue()          # Items in queue have format ({fleets location}, last fleet location)
    dest_paths = {}             # Dict with dest as key and a list of all paths from start_location to dest as value

    # We need to start on a coast / port
    if map_object.area_type(start_location) not in ('COAST', 'PORT') or '/' in start_location:
        return []

    # Queuing all adjacent water locations from start
    for loc in [loc.upper() for loc in map_object.abut_list(start_location, incl_no_coast=True)]:
        if map_object.area_type(loc) in ['WATER', 'PORT']:
            to_check.put(({loc}, loc))

    # Checking all subsequent adjacencies until no more adjacencies are possible
    while not to_check.empty():
        fleets_loc, last_loc = to_check.get()

        # Checking adjacencies
        for loc in [loc.upper() for loc in map_object.abut_list(last_loc, incl_no_coast=True)]:

            # If we find adjacent coasts, we mark them as a possible result
            if map_object.area_type(loc) in ('COAST', 'PORT') and '/' not in loc and loc != start_location:
                dest_paths.setdefault(loc, [])

                # If we already have a working path that is a subset of the current fleets, we can skip
                # Otherwise, we add the new path as a valid path to dest
                for path in dest_paths[loc]:
                    if path.issubset(fleets_loc):
                        break
                else:
                    dest_paths[loc] += [fleets_loc]

            # If we find adjacent water/port, we add them to the queue
            elif map_object.area_type(loc) in ('WATER', 'PORT') \
                    and loc not in fleets_loc \
                    and len(fleets_loc) < max_convoy_length:
                to_check.put((fleets_loc | {loc}, loc))

    # Merging destinations with similar paths
    similar_paths = {}
    for dest, paths in dest_paths.items():
        for path in paths:
            tuple_path = tuple(sorted(path))
            similar_paths.setdefault(tuple_path, set([]))
            similar_paths[tuple_path] |= {dest}

    # Converting to list
    results = []
    for fleets, dests in similar_paths.items():
        results += [(start_location, set(fleets), dests)]

    # Returning
    queue.put(1)
    return results

def build_convoy_paths_cache(map_object, max_convoy_length):
    """ Builds the convoy paths cache for a map
        :param map_object: The instantiated map object
        :param max_convoy_length: The maximum convoy length permitted
        :return: A dictionary where the key is the number of fleets in the path and
                 the value is a list of convoy paths (start loc, {fleets}, {dest}) of that length for the map
        :type map_object: diplomacy.Map
    """
    print('Generating convoy paths for {}'.format(map_object.name))
    coasts = [loc.upper() for loc in map_object.locs
              if map_object.area_type(loc) in ('COAST', 'PORT') if '/' not in loc]

    # Starts the progress bar loop
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    progress_bar = threading.Thread(target=display_progress_bar, args=(queue, len(coasts)))
    progress_bar.start()

    # Getting all paths for each coasts in parallel
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    tasks = [(map_object, coast, max_convoy_length, queue) for coast in coasts]
    results = pool.starmap(get_convoy_paths, tasks)
    pool.close()
    results = [item for sublist in results for item in sublist]
    queue.put(None)
    progress_bar.join()

    # Splitting into buckets
    buckets = collections.OrderedDict({i: [] for i in range(1, len(map_object.locs) + 1)})
    for start, fleets, dests in results:
        buckets[len(fleets)] += [(start, fleets, dests)]

    # Returning
    print('Found {} convoy paths for {}\n'.format(len(results), map_object.name))
    return buckets

def get_file_md5(file_path):
    """ Calculates a file MD5 hash
        :param file_path: The file path
        :return: The computed md5 hash
    """
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def add_to_cache(map_name):
    """ Lazy generates convoys paths for a map and adds it to the disk cache
        :param map_name: The name of the map
        :return: The convoy_paths for that map
    """
    disk_convoy_paths = {'__version__': __VERSION__}        # Uses hash as key

    # Loading cache from disk (only if it's the correct version)
    if os.path.exists(DISK_CACHE_PATH):
        try:
            cache_data = pickle.load(open(DISK_CACHE_PATH, 'rb'))
            if cache_data.get('__version__', '') != __VERSION__:
                print('Upgrading cache from "%s" to "%s"' % (cache_data.get('__version__', '<N/A>'), __VERSION__))
            else:
                disk_convoy_paths.update(cache_data)

        # Invalid pickle file - Rebuilding
        except (pickle.UnpicklingError, EOFError):
            pass

    # Getting map MD5 hash
    map_path = os.path.join(settings.PACKAGE_DIR, 'maps', map_name + '.map')
    if not os.path.exists(map_path):
        return None
    map_hash = get_file_md5(map_path)

    # Determining the depth of the search (small maps can have larger depth)
    max_convoy_length = SMALL_MAPS_CONVOY_LENGTH if map_name in SMALL_MAPS else ALL_MAPS_CONVOY_LENGTH

    # Generating and adding to alternate cache paths
    if map_hash not in disk_convoy_paths:
        map_object = Map(map_name, use_cache=False)
        disk_convoy_paths[map_hash] = build_convoy_paths_cache(map_object, max_convoy_length)
        os.makedirs(os.path.dirname(DISK_CACHE_PATH), exist_ok=True)
        pickle.dump(disk_convoy_paths, open(DISK_CACHE_PATH, 'wb'))

    # Returning
    return disk_convoy_paths[map_hash]

def get_convoy_paths_cache():
    """ Returns the current cache from disk """
    disk_convoy_paths = {}                  # Uses hash as key
    cache_convoy_paths = {}                 # Use map name as key

    # Loading cache from disk (only if it's the correct version)
    if os.path.exists(DISK_CACHE_PATH):
        try:
            cache_data = pickle.load(open(DISK_CACHE_PATH, 'rb'))
            if cache_data.get('__version__', '') == __VERSION__:
                disk_convoy_paths.update(cache_data)
        except (pickle.UnpicklingError, EOFError):
            pass

    # Getting map name and file paths
    files_path = glob.glob(settings.PACKAGE_DIR + '/maps/*.map')
    for file_path in files_path:
        map_name = file_path.replace(settings.PACKAGE_DIR + '/maps/', '').replace('.map', '')
        map_hash = get_file_md5(file_path)
        if map_hash in disk_convoy_paths:
            cache_convoy_paths[map_name] = disk_convoy_paths[map_hash]

    # Returning
    return cache_convoy_paths
