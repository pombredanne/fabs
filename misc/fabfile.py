import os

from burlap import util
from burlap.apt import Apt
from fabric.api import *


LEIN_URL = "https://raw.github.com/technomancy/leiningen/preview/bin/lein"
GOLANG_URL = "http://go.googlecode.com/files/go1.0.3.linux-amd64.tar.gz"
RESOURCE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/resources"

apt = Apt(RESOURCE_PATH)


# press up and down to scroll and q during rvm ruby install
@task
def install_rvm(install_ruby_version=None):
  run("\curl https://raw.github.com/wayneeseguin/rvm/master/binscripts/rvm-installer | bash -s stable")

  apt.apt_install("build-essential openssl libreadline6 libreadline6-dev curl git zlib1g zlib1g-dev libssl-dev libyaml-dev libsqlite3-dev sqlite3 libxml2-dev libxslt-dev autoconf libc6-dev ncurses-dev automake libtool bison subversion pkg-config")

  if install_ruby_version:
    run("rvm install %s" % install_ruby_version)


@task
def install_lein():
  with settings(warn_only=True):
    run("mkdir $HOME/bin")

  with cd("$HOME/bin"):
    run("wget %s -O lein" % LEIN_URL)
    util.chmod("$HOME/bin/lein", "+x")


@task
def install_haskell_platform():
  apt.apt_install("haskell-platform haskell-platform-doc haskell-platform-prof")


@task
def install_golang():
  install_folder = "$HOME/software/go"

  with settings(warn_only=True):
    run("mkdir $HOME/software")

  util.remote_archive(GOLANG_URL, install_folder)

  # add to path
  run("echo '' >> $HOME/.bashrc" )
  run("echo '# automatically added by install_golang' >> $HOME/.bashrc" )
  run("echo 'export GOROOT=%s' >> $HOME/.bashrc" % install_folder)
  run("echo 'export PATH=$PATH:$GOROOT/bin' >> $HOME/.bashrc")
  run("echo '# end' >> $HOME/.bashrc" )