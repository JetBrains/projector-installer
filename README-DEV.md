This file contains information useful only for persons 
who are trying to install projector-installer from sources and/or 
to build own wheel file.  

Warning! For experiments do not forget to create 
```commandline 
python3 -m venv venv
```
and activate
```commandline
source ./venv/bin/activate 
```
virtual environment.  

### install from source 
```shell script
git clone https://github.com/JetBrains/projector-installer.git
cd projector-installer
pip3 install -r requirements.txt 
python3 setup.py bundle
pip3 install .
```

## Build python wheel file
```shell script
pip3 install wheel
rm -r projector_installer/bundled dist build  # Remove old build files
python3 setup.py bundle bdist_wheel
```

### install from wheel file 
```shell script
pip3 install projector_installer-VERSION-py3-none-any.whl
```

## Publish
```shell script
rm -r projector_installer/bundled dist build  # Remove old build files
python3 setup.py bundle sdist bdist_wheel  # Build required files
python3 -m twine upload --repository testpypi --verbose dist/*  # Upload to https://test.pypi.org/project/projector-installer/
python3 -m twine upload dist/*  # Upload to https://pypi.org/project/projector-installer/
```