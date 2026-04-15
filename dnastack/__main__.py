"""Legacy entry point — delegates to the omics CLI."""
import sys

from dnastack.omics_cli import omics as dnastack

if __name__ == "__main__":
    dnastack.main(prog_name=sys.argv[0])
