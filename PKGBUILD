#Maintainer: "Yannick LM <yannicklm1337 AT gmail DOT com>"

pkgname=pycp-git
pkgver=20100627
pkgrel=1
pkgdesc="cp and mv with a progressbar"
url="http://sd-5791.dedibox.fr/prog/pycp.txt"
arch=('any')
license=('GPL')
depends=('python-progressbar')
makedepends=('git' 'python' 'help2man')
replaces=('pycp')

_gitroot="git://github.com/yannicklm/pycp.git"
_gitname="pycp"

build() {
  cd ${srcdir}
  msg "Connecting to github server...."

  if [ -d ${srcdir}/$_gitname ] ; then
    cd $_gitname && git pull origin
    msg "The local files are updated."
  else
    git clone $_gitroot
  fi

  msg "GIT checkout done or server timeout"
  msg "Starting make..."

  git clone $_gitname $_gitname-build
  cd ${srcdir}/$_gitname-build
  python setup.py install --root=$startdir/pkg || return 1
}

