import os

from burlap import util
from burlap.apt import Apt
from fabric.api import *


AKKA_URL = "http://download.akka.io/downloads/akka-2.0.4.tgz"
GOLANG_URL = "http://go.googlecode.com/files/go1.0.3.linux-amd64.tar.gz"
LEIN_URL = "https://raw.github.com/technomancy/leiningen/preview/bin/lein"
LEVELDB_URL = "http://leveldb.googlecode.com/files/leveldb-1.7.0.tar.gz"
SBT_URL = "http://scalasbt.artifactoryonline.com/scalasbt/sbt-native-packages/org/scala-sbt/sbt//0.12.1/sbt.deb"
SCALA_URL = "http://www.scala-lang.org/downloads/distrib/files/scala-2.9.2.deb"
SNAPPY_URL = "http://snappy.googlecode.com/files/snappy-1.0.5.tar.gz"
VERTX_URL = "http://vertx.io/downloads/vert.x-1.3.0.final.tar.gz"

RESOURCE_PATH = os.path.dirname(os.path.realpath(__file__)) + "/resources"

apt = Apt(RESOURCE_PATH)


# press up and down to scroll and q during rvm ruby install
@task
def install_rvm(install_ruby_version=None):
  run("\curl https://raw.github.com/wayneeseguin/rvm/master/binscripts/rvm-installer | bash -s stable")

  apt.apt_install("build-essential openssl libreadline6 libreadline6-dev curl git zlib1g zlib1g-dev libssl-dev libyaml-dev libsqlite3-dev sqlite3 libxml2-dev libxslt-dev autoconf libc6-dev ncurses-dev automake libtool bison subversion pkg-config")

  run("echo '' >> $HOME/.profile")
  run("echo '# grepped from .bash_profile' >> $HOME/.profile")
  run("grep rvm $HOME/.bash_profile >> $HOME/.profile")
  run("echo '# end' >> $HOME/.profile")
  run("mv $HOME/.bash_profile $HOME/.bash_profile_`date +%Y%m%d%H%M`")

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
  run("echo '' >> $HOME/.bashrc" )
  run("echo '# automatically added by install_haskell_platform' >> $HOME/.bashrc" )
  run("echo 'export PATH=$PATH:$HOME/.cabal/bin' >> $HOME/.bashrc")
  run("echo '# end' >> $HOME/.bashrc" )


@task
def install_golang(golang_url=GOLANG_URL):
  install_folder = "$HOME/software/go"

  with settings(warn_only=True):
    run("mkdir $HOME/software")

  util.remote_archive(golang_url, install_folder)

  # add to path
  run("echo '' >> $HOME/.bashrc" )
  run("echo '# automatically added by install_golang' >> $HOME/.bashrc" )
  run("echo 'export GOROOT=%s' >> $HOME/.bashrc" % install_folder)
  run("echo 'export PATH=$PATH:$GOROOT/bin' >> $HOME/.bashrc")
  run("echo '# end' >> $HOME/.bashrc" )


@task
def install_nodejs():
  apt.add_apt_repository("ppa:chris-lea/node.js")
  apt.apt_update()
  apt.apt_install("nodejs npm nodejs-dev")


@task
def leveldb(leveldb_url=LEVELDB_URL, use_snappy=True):
  snappy()

  if util.dir_exists("$HOME/lib/leveldb"):
    print "leveldb already exists in $HOME/lib/leveldb"
    return

  with settings(warn_only=True):
    run("mkdir $HOME/lib")

  basename = os.path.basename(leveldb_url).replace(".tar.gz", "")
  dest_path = "$HOME/lib/" + basename
  util.remote_archive(leveldb_url, dest_path)
  with cd(dest_path):
    if use_snappy:
      run("CXXFLAGS=\"-I ~/lib/snappy -L ~/lib/snappy/.libs/\" make all")
    else:
      run("make all")

  with cd("$HOME/lib"):
    run("ln -s -f %s leveldb" % basename)

  print "headers: $HOME/lib/leveldb/include/leveldb"
  print "libs: $HOME/lib/leveldb"


@task
def snappy(snappy_url=SNAPPY_URL, install=False):
  if util.dir_exists("$HOME/lib/snappy"):
    print "snappy already exists in $HOME/lib/snappy"
    return

  with settings(warn_only=True):
    run("mkdir $HOME/lib")

  basename = os.path.basename(snappy_url).replace(".tar.gz", "")
  dest_path = "$HOME/lib/" + basename
  util.remote_archive(snappy_url, dest_path)
  with cd(dest_path):
    run("./configure")
    run("make")
    if install:
      sudo("make install")

  with cd("$HOME/lib"):
    run("ln -s -f %s snappy" % basename)

  with cd("$HOME/lib/%s" % basename):
    run("./snappy_unittest")

  print "headers: $HOME/lib/snappy"
  print "libs: $HOME/lib/snappy/.lib"


@task
def install_scala(scala_url=SCALA_URL, tmp_dir="/tmp"):
  basename = os.path.basename(scala_url)
  with cd(tmp_dir):
    run("wget %s -O %s" % (scala_url,basename))
    apt.apt_install("libjansi-java")
    sudo("dpkg -i %s" % basename)


@task
def install_akka(akka_url=AKKA_URL):
  with settings(warn_only=True):
    run("mkdir $HOME/software")
    run("mkdir $HOME/bin")

  basename = os.path.basename(akka_url).replace(".tgz", "")
  install_folder = "$HOME/software/%s" % basename
  akka_bin = "%s/bin/akka" % install_folder
  util.remote_archive(akka_url, install_folder)

  # set AKKA HOME to install directory
  run("sed -i 's/^declare AKKA_HOME/#declare AKKA_HOME/g' %s" % \
      akka_bin)
  run("sed -i '/^#declare AKKA_HOME/ a\\AKKA_HOME=%s' %s" % \
      ("$HOME/software/akka", akka_bin))
  
  with cd("$HOME/software"):
    run("ln -s %s %s" % (basename, "akka"))

  with cd("$HOME/bin"):
    run("ln -s %s ." % "$HOME/software/akka/bin/akka")


@task
def install_sbt(sbt_url=SBT_URL, tmp_dir="/tmp"):
  basename = os.path.basename(sbt_url)
  with cd(tmp_dir):
    run("wget %s -O %s" % (sbt_url,basename))
    sudo("dpkg -i %s" % basename)


@task
def install_vertx(vertx_url=VERTX_URL):
  with settings(warn_only=True):
    run("mkdir $HOME/software")
    run("mkdir $HOME/bin")

  basename = os.path.basename(vertx_url).replace(".tar.gz", "")
  install_folder = "$HOME/software/%s" % basename
  util.remote_archive(vertx_url, install_folder)

  with cd("$HOME/software"):
    run("ln -s %s %s" % (basename, "vertx"))

  with cd("$HOME/bin"):
    run("ln -s %s ." % "$HOME/software/vertx/bin/vertx")
