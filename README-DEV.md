# projector-installer developer README
This file contains information useful only for person 
who is trying to install projector-installer from source and/or 
to build own wheel file.  

# Table of Contents
1. [Prepare environment](#Prepare-environment) 
2. [Install from source](#Install-from-source)
3. [Create python wheel file](#Create-python-wheel-file)
4. [Install from wheel file](#Install-from-wheel-file)
5. [Publish](#Publish)
6. [Using specific server version](#Using-specific-server-version)
 
## Prepare environment<a id="Prepare-environment"></a>
For experiments, you may want to use virtual environment.
To use it you have to install python3-venv package first:
 ```commandline
sudo apt install python3-venv
```

Virtual environment can be created and activated using the following commands:  
```commandline 
python3 -m venv venv
source ./venv/bin/activate 
```

If you are running Ubuntu 18.04 or earlier distributive it is necessary to upgrade pip
with command:
```commandline
python3 -m pip install -U pip 
```

To leave virtual environment use command
```commandline
deactivate
```

## Install from source<a id="Install-from-source"></a>
```shell script
# clone project-installer repository  
git clone https://github.com/JetBrains/projector-installer.git
# go to source directory
cd projector-installer
# install dependencies  
pip3 install -r requirements.txt
# get bundled files 
python3 setup.py bundle
# do install 
pip3 install .
```

## Create python wheel file<a id="Create-python-wheel-file"></a>
From projector-installer source directory execute:
```shell script
# install dependencies
pip3 install -r requirements.txt
# Remove old files if necessary 
rm -rf dist build
# get bundled files and create wheel   
python3 setup.py bundle bdist_wheel
```

A `whl` file will be created in the `dist` dir.

## Install from wheel file<a id="Install-from-wheel-file"></a>
To install projector-installer from wheel file use command:
```shell script
pip3 install projector_installer-VERSION-py3-none-any.whl
```

You can download a built `whl` file from [Releases](https://github.com/JetBrains/projector-installer/releases) or build it yourself.

## Publish<a id="Publish"></a>

```shell script
rm -rf dist build  # Remove old build files if necessary
pip3 install -r requirements.txt # install requirements if necessary
python3 setup.py bundle sdist bdist_wheel  # Build required files
python3 -m twine upload --repository testpypi --verbose dist/*  # Upload to https://test.pypi.org/project/projector-installer/
python3 -m twine upload dist/*  # Upload to https://pypi.org/project/projector-installer/
```

## Using specific server version<a id="Using-specific-server-version"></a>
Projector server used by installer retrieved when bundle setup command is executed. 
User can specify desired server distribution by modifying PROJECTOR_SERVER_URL 
variable in setup.py script. Usually this variable points to some official server release, 
for example: 

```python
PROJECTOR_SERVER_URL: str = 'https://github.com/JetBrains/projector-server/releases/' \
                            'download/v1.2.1/projector-server-v1.2.1.zip'
```

Starting from installer newer than ver. 1.2.1 it is possible 
to specify local file in this variable, for example:

```python
PROJECTOR_SERVER_URL: str = 'file:///path/to/local/server/build/projector-server-v1.2.1.zip'
```

Server distribution can be build using [these](https://github.com/JetBrains/projector-server/blob/master/README.md#building)
instructions.