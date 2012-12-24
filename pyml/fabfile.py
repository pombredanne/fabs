from functools import partial
import hashlib
import os

from fabric.api import *
from fabric.contrib import files

from burlap import util
from burlap.apt import Apt

VIRTUAL_ENV = "$HOME/pyml"
RESOURCE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/resources"

apt = Apt(RESOURCE_PATH)

@task
def install_all(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_virtualenv(virtualenv)
  install_numpy(virtualenv, upgrade)
  install_scipy(virtualenv, upgrade)
  install_matplotlib(virtualenv, upgrade)
  install_pandas(virtualenv, upgrade)
  install_statsmodels(virtualenv, upgrade)
  install_pytables(virtualenv, upgrade)
  install_scikit_learn(virtualenv, upgrade)
  install_ipython(virtualenv, upgrade)
  install_ipython_notebook(virtualenv, upgrade)

@task
def is_virtualenv_installed(virtualenv=VIRTUAL_ENV):
  if virtualenv_installed():
    print "virtual env exists: ", VIRTUAL_ENV
    return true
  else:
    print "virtual env does not exist: ", VIRTUAL_ENV
    return false

@task
def install_virtualenv(virtualenv=VIRTUAL_ENV):
  if not virtualenv_installed():
    run("virtualenv %s" % VIRTUAL_ENV)
    pip_install(virtualenv, "pip", upgrade=True)

@task
def installed_site_packages(virtualenv=VIRTUAL_ENV):
  pip(virtualenv, "freeze")
 
@task
def install_base(virtualenv=VIRTUAL_ENV):
  apt.apt_install("gcc g++ python-dev")

@task
def install_numpy(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  pip_install(virtualenv, "numpy", upgrade=upgrade)

@task
def install_scipy(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  apt.apt_install("libblas-dev liblapack-dev libatlas-dev gfortran")
  pip_install(virtualenv, "scipy", upgrade=upgrade)

@task
def install_pandas(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  pip_install(virtualenv, "pandas", upgrade=upgrade)

@task
def install_statsmodels(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  pip_install(virtualenv, "statsmodels", upgrade=upgrade)

@task
def install_pytables(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  apt.apt_install("libhdf5-serial-1.8.4 libhdf5-serial-dev")
  pip_install(virtualenv, "numexpr", upgrade=upgrade)
  pip_install(virtualenv, "cython", upgrade=upgrade)
  pip_install(virtualenv, "tables", upgrade=upgrade)

@task
def install_scikit_learn(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  pip_install(virtualenv, "scikit-learn", upgrade=upgrade)

@task
def install_matplotlib(virtualenv=VIRTUAL_ENV, upgrade=False):
  install_base()
  apt.apt_install("libfreetype6 libfreetype6-dev libpng12-0 libpng12-dev")
  pip_install(virtualenv, "matplotlib", upgrade=upgrade)

@task
def install_ipython(virtualenv=VIRTUAL_ENV, upgrade=False):
  pip_install(virtualenv, "ipython", upgrade=upgrade)

"""
IPython Notebook
http://ipython.org/ipython-doc/dev/interactive/htmlnotebook.html 
http://ipython.org/ipython-doc/dev/install/install.html#installnotebook
"""

ipython_nb_root = "$HOME/ipython_notebook"
ipython_nb_pid = "%s/pid" % ipython_nb_root
ipython_nb_log = "%s/log" % ipython_nb_root
ipython_nb_notebook_path = "%s/notebooks" % ipython_nb_root
ipython_nb_start = "$HOME/bin/start_ipython_notebook"
ipython_nb_stop = "$HOME/bin/stop_ipython_notebook"

@task
def install_ipython_notebook(virtualenv=VIRTUAL_ENV, upgrade=False):
  apt.apt_install("libzmq1 libzmq-dev libzmq-dbg")
  pip_install(virtualenv, "tornado", upgrade=upgrade)
  pip_install(virtualenv, "pyzmq", upgrade=upgrade)
  install_ipython_mathjax(virtualenv)
  setup_ipython_nb_paths()
  setup_ipython_scripts(virtualenv)
  configure_ipython_notebook()

def install_ipython_mathjax(virtualenv=VIRTUAL_ENV):
  script = "from IPython.external.mathjax import install_mathjax\ninstall_mathjax()"
  h = hashlib.md5()
  h.update(script)
  scriptname = "$HOME/%s" % h.hexdigest()
  run("printf \"%s\" > %s" % (script,scriptname))
  run("%s/bin/python %s" % (virtualenv, scriptname))

def setup_ipython_nb_paths():
  with settings(warn_only=True):
    run("mkdir %s" % ipython_nb_root)
    run("mkdir %s" % ipython_nb_notebook_path)

def setup_ipython_scripts(virtualenv=VIRTUAL_ENV, port=8987):
  util.put_template(RESOURCE_PATH + "/start_ipython_notebook.jinja2", \
      {"virtualenv": virtualenv, "port": port, \
      "logfile": ipython_nb_log, "pidfile": ipython_nb_pid}, \
      ipython_nb_start, permissions="+x")

  util.put_template(RESOURCE_PATH + "/stop_ipython_notebook.jinja2", \
      {"pidfile": ipython_nb_pid}, ipython_nb_stop, permissions="+x")

def configure_ipython_notebook(virtualenv=VIRTUAL_ENV):
  ipython_config = "$HOME/.ipython/profile_nbserver/ipython_notebook_config.py"
  if not files.exists(ipython_config):
    home_path = util.home_path()
    run("%s/bin/ipython profile create nbserver" % virtualenv)
    run("echo \"c.IPKernelApp.pylab = 'inline'\" >> %s" % ipython_config)
    run("echo \"c.NotebookApp.ip = '*'\" >> %s" % ipython_config)
    run("echo \"c.NotebookApp.open_browser = False\" >> %s" % ipython_config)
    run("echo \"c.NotebookManager.notebook_dir = u'%s/ipython_notebook/notebooks'\" >> %s" % (home_path, ipython_config))

@task
def ipython_start(virtualenv=VIRTUAL_ENV):
  run(ipython_nb_start, pty=False)

@task
def ipython_stop(virtualenv=VIRTUAL_ENV):
  run(ipython_nb_stop)

@task
def ipython_status(virtualenv=VIRTUAL_ENV):
  run("cat %s" % ipython_nb_pid)


"""
Helper Functions
"""

def virtualenv_installed(virtualenv=VIRTUAL_ENV):
  return files.exists("%s/bin/activate" % virtualenv)

def pip(virtualenv, cmd):
  run("%s/bin/pip %s" % (virtualenv, cmd))

def pip_install(virtualenv, package, upgrade=False):
  cmd = "install -U %s" % package if upgrade else "install %s" % package
  pip(virtualenv, cmd)