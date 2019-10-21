"""
Removes an experiment from the Crayon Docker server.
Argument 1: the name of the experiment to remove.
"""
import pycrayon
import sys


def main():
    """ Opens the crayon client and removes the specified experiment."""
    crayon_client = pycrayon.CrayonClient("localhost")
    crayon_client.remove_experiment(sys.argv[1])


if __name__ == "__main__":
    main()
