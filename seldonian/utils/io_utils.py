import os
import pickle
import json

def dir_path(path):
    """ A utility for checking whether a path is a directory

    :param path: An input path that may or may not be a directory
    :type path: str
    """
    if os.path.isdir(path):
        return path
    else:
        raise NotADirectoryError(path)

def load_pickle(filename):
    """ A wrapper for loading an object from a pickle file

    :param filename: A filename pointing to a pickle file
    :type filename: str
    """
    with open(filename,'rb') as infile:
        data = pickle.load(infile)
    return data

def save_pickle(filename,data,verbose=False):
    """ A wrapper for saving an object to a pickle file

    :param filename: A filename for the saved pickle file
    :type filename: str

    :param data: The object you want to pickle
    :type data: Pickle-able object
    """
    with open(filename,'wb') as outfile:
        pickle.dump(data,outfile,protocol=pickle.HIGHEST_PROTOCOL)
        if verbose:
            print(f"Saved {filename}\n")

def load_json(filename):
    """ A wrapper for loading an object from a JSON file

    :param filename: An input filename pointing to a JSON file
    :type filename: str
    """
    with open(filename,'r') as infile:
        data = json.load(infile)
    return data

def save_json(filename,data,indent=2,verbose=False):
    """ A wrapper for loading an object from a JSON file

    :param filename: An input filename pointing to a JSON file
    :type filename: str
    """
    with open(filename,'w') as outfile:
        data = json.dump(data,outfile)
    if verbose:
        print(f"Saved {filename}\n")

def load_supervised_metadata(filename):
    """ Load metadata from JSON file into a dictionary """
    metadata_dict = load_json(filename)
    regime = metadata_dict['regime']
    columns = metadata_dict['columns']
    assert regime == 'supervised_learning'
    sensitive_columns = metadata_dict['sensitive_columns']
    sub_regime = metadata_dict['sub_regime']
    return regime, sub_regime, columns, sensitive_columns
    