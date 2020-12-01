# projector-installer developer README
This file contains information useful only for person 
who is trying to install projector-installer from source and/or 
to build own wheel file.  

# Table of Contents
1. [Setup virtual environment](#Setup-virtual-environment) 
2. [Install from source](#Install-from-source)
3. [Create python wheel file](#Create-python-wheel-file)
4. [Install from wheel file](#Install-from-wheel-file)
5. [Publish](#Publish)
 
## Setup virtual environment
For experiments you may want to use virtual environment.
To use it you have to install python3-venv package first:
 ```commandline
sudo apt install python3-venv
```

Virtual environment can be created and activated using the following commands:  
```commandline 
python3 -m venv venv
source ./venv/bin/activate 
```

To leave virtual environment use command
```commandline
deactivate
``` 

## Install from source 
```shell script
git clone https://github.com/JetBrains/projector-installer.git
cd projector-installer
pip3 install -r requirements.txt 
python3 setup.py bundle
pip3 install .
```

## Create python wheel file
```shell script
pip3 install -r requirements.txt 
rm -r dist build  # Remove old build files if necessary
python3 setup.py bundle bdist_wheel
```

## Install from wheel file 
```shell script
pip3 install projector_installer-VERSION-py3-none-any.whl
```

## Publish
```shell script
rm -r dist build  # Remove old build files
python3 setup.py bundle sdist bdist_wheel  # Build required files
python3 -m twine upload --repository testpypi --verbose dist/*  # Upload to https://test.pypi.org/project/projector-installer/
python3 -m twine upload dist/*  # Upload to https://pypi.org/project/projector-installer/
```