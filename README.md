# labelimg_OBB_shortcut
refer https://github.com/heshameraqi/labelImg_OBB for installation.
Or tested envs (ubuntu18.04, anaconda, python3.8) as follow:
  1. install pyqt5: sudo apt-get install pyqt5-dev-tools
  2. pip install -r requirements/requirements-linux-python3.txt
  3. make qt5py3
  4. start labeling: python3 labelImg.py



With keyboard shortcut for fast fine tuning the labels.

w = add new bbox

ctrl+j = edit mode

direction key = translation bbox

# added

rotation bbox:

  o = +0.1
  
  p = -0.1
  
  k = +1
  
  l = -1
  
  m = +5
  
  , = -5

For small scale data, use 1/3/5 degree labeling is sufficient enough (modify libs/canvas_shortcut.py).
Directly show the area of current bbox and angle instead of [width, height], because we need the smallest label.
