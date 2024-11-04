import streamlit as st
import streamlit.runtime.scriptrunner.magic_funcs
import streamlit.web.cli as stcli
from streamlit_js_eval import streamlit_js_eval
import pandas
import glob
from io import BytesIO
import os
import subprocess
import sys
import time
import openpyxl
from datetime import datetime
import binpacking
##

def resolve_path(path):
    resolved_path = os.path.abspath(os.path.join(os.getcwd(), path))
    return resolved_path


if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("main.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())