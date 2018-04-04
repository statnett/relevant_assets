# InfluenceComputation
A script compliant with EU's SOGL to assess influence of external elements on a grid model. Supports UCTE DEF CGM as well as import from PSSE.

# Introduction
European TSOs are required by European Commission Regulation (EU) 2017/1485 of 2 August 2017 establishing a guideline on electricity transmission system operation to develop a methodology to assess the influence on their system of elements located in another TSO's control area. This script was developed as a proposal for an implementation of a methodology that should be compliant with SOGL's requirements and provides a flexible implementation. The script is a modification and refactoring of the script by Jonathan Baudier (available at <https://github.com/JonathanBaudier/InfluenceComputation>, released under apache license v2). Major changes:
* support for PSSE file format
* extensive refactoring and testing to improve robustness and increase reusability
* some speed improvements

This version is released under Apache license to match Jonathan's earlier script, see license file.

# Requirements
To be able to run the code fully, you will need the following:
* A working legacy Python (Python 2) installation
* A working Python installation
* A licensed version of PSSE installed (you should be able to run UCTE definition files without this requirement, but the tests for the PSSE file will fail as it needs access to the PSSE API to read the test file.)  
* Several python packages installed in legacy Python and Python, see below for more details.

This script should be compatible with any grid model compliant with UCTE data exchange format (UCTE DEF) version 2 (http://cimug.ucaiug.org/Groups/Model%20Exchange/UCTE-format.pdf). However, for large grid size (around 8 000 nodes, 13 000 branches for Continental Europe's Synchronous Area), a large memory space is required. Thus, for this kind of grid 8 GB of RAM are required (16 GB recommended).

The script should also be compatible with grid models in PSSE33. It uses a wrapper around the PSSE python API to get access to the grid topology and gather the relevant information. A complication when using PSSE33 is that it does not support Python 3, while the script is written in Python 3.6. To solve this, the Python 3 process starts a Python 2 process and interfaces using the execnet package. This means, however, that both a working Python 2 and Python 3 interpreter needs to be available on your system to be able to use this functionality.

## Installation notes
0. Ensure you have PSSE33 installed, as well as Python 2.7 in folder `C:\Python27`, and a python 3 installation. 
1. Install necessary Python 3 packages using `pipenv` ([docs](https://docs.pipenv.org/install/#installing-pipenv)) with command `pipenv install --dev`
3. Get python 2 ready for PSSE is a bit tricky as there are bugs in the default installation. Do the following to fix this: 
    1. Uninstall the buggy versions:
        1. in a command prompt, navigate to `C:\Python27`
        2. uninstall old numpy, scipy, tables: `python -m pip uninstall numpy`, `python -m pip uninstall scipy`, `python -m pip uninstall tables`
    2. reinstall numpy, scipy, tables precompiled version:
        1. Go to <https://www.lfd.uci.edu/~gohlke/pythonlibs/> and download the right wheel files:
            1. Numpy: `numpy-1.14.2+mkl-cp27-cp27m-win32.whl`
            2. Scipy: `scipy-1.0.0-cp27-cp27m-win32.whl`
            3. Pytables: `tables-3.4.2-cp27-cp27m-win32.whl`
            (this to get rid of a buggy version of pytables in the default python 2 install)
        2. in a command prompt, navigate to `C:\Python27`
        3. install numpy, scipy and tables (in that order!!!) with a command like `python -m pip install C:\Users\yourusername\Downloads\numpy\numpy-1.14.2+mkl-cp27-cp27m-win32.whl` and something similar for scipy and tables.
    3. install other packages:
        1. in your command promtp, navigate to `C:\Python27`
        2. install requirements_27.txt: `python -m pip install -r C:\path_to_your_repo\requirements_27.txt`         
            
4. Try to run all the tests using `pytest`. The model provides two test files: the UCTE model for Europe as provided in Jonathan's original script, and a IEEE 300 bus test model (taken from <http://icseg.iti.illinois.edu/ieee-300-bus-system/>, saved as `.sav` file, and added dummy line ratings.) The tests should take about 2 minutes, and will among others test a full run using the 300 bus test model.

## How to run an existing model with different settings
For example, you want to run `example.uct` with different settings:
0. Ensure your installation is correct and all tests run, see installation notes above.
1. Open the file `settings.py` and check where the settings for example.uct are defined. in this case, on line 8 to 28.
2. Make the changes you want to those settings.
3. Note the name of the settings set (in this case UCT0, see line 8)
4. Open the file `main.py`, scroll to the last line, and set to the right settings: `main(settings=get_settings(SettingsEnum.UCT0))`
5. run the script by running main.py.
6. inspect the results that will appear in a subfolder *output_files*.

## How to run a new model with copied settings
For example, you want to run `my_ieee_model.sav` from PSSE, using the same settings as used in setting set `PSSE0`.
0. Ensure your installation is correct and all tests run, see installation notes above.
1. Open the file `settings.py` and check where the settings `PSSE0` are defined. in this case, on line 30 to 40.
2. Copy and paste this setting set with a new name. For example, we call it `myPSSEsettings`: then you copy line 30 to 40 and paste it on line 41, changing the name `SettingsEnum.PSSE0` to `SettingsEnum.myPSSEsettings`. Change also the following:
    1. input_file_name should be `my_ieee_model.sav`
    2. case_name should be `Nordics` if you use a model that is a variant of to the Nordics model that you chose. If so, the countries will be set up correctly automatically. If you have a totally new model with a different country setup, pick another case_name.
    3. countries should match the set of countries you are interested in. If you have a different country setup, then you have to make changes to the set_country functions in the code - see there when relevant. 
    4. other settings should be defined as you wish, see settings.py for documentation on their meaning. 
3. On line 3, extend the enum with your new name `myPSSEsettings`.
4. Open the file `main.py`, scroll to the last line, and set to the right settings: `main(settings=get_settings(SettingsEnum.myPSSEsettings))`
5. run the script by running main.py.
6. inspect the results that will appear in a subfolder *output_files*.



# How influence is defined
For each grid element located outside of the investigated control area, the influence is defined as the maximum Line Outage Distribution Factor on any element located in the investigated control area in any N-i situation in which an i element is disconnected.
For each grid element located outside of the investigated control area, the influence is defined as the maximum Line Outage Distribution Factor on any element located in the investigated control area in any N-i situation in which an i element is disconnected multiplied by the ratio of MVA thermal limits of the investigated element and the influenced element.

# Implementation details for PSSE read-in:
* What to read: all elements over 80 kV plus generators behind step-up transformer are read (this can be adapted in the settings)
* We use Rate A from PSSE as PATL
* multi-section lines are combined into one branch
* Bus bar couplers:
    * All lines with rate 0 defined as bus bar couplers
* Transformers:
    * 3-winding transformers:
        * if 0 to 1 branches relevant: skip
        * if 2 branches relevant: change to 2w
        * if 3 branches relevant 3 2w transformers with dummy bus (as in PSSE acc to doc)

# Known bugs, missing features etc
* Code for generator IF calculation is not sped up with numba yet and takes a disproportionately long time to run. My first try to get numba to speed up this code failed, not tried another yet.
* Handling of unicode names is sloppy at best, should be improved later.
