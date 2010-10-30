#Maintainer: "Yannick LM <yannicklm1337 AT gmail DOT com>"

pkgname=pycp-git
pkgver=20101030
pkgrel=1
pkgdesc="cp and mv with a progressbar"
url="http://github.com/yannicklm/pycp"
arch=('any')
license=('MIT')
depends=('python2')
makedepends=('git' 'python2' 'help2man')
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
    git clone $_gitroot $_gitname
  fi

  msg "GIT checkout done or server timeout"
  msg "Starting make..."

  rm -rf "$srcdir/$_gitname-build"
  git clone $_gitname $_gitname-build
  cd ${srcdir}/$_gitname-build
  python2 setup.py build

}

package() {
  cd ${srcdir}/$_gitname-build
  python2 setup.py install --root=$pkgdir/ --optimize=1
  mkdir -p $pkgdir/usr/share/licenses/pycp
  install COPYING $pkgdir/usr/share/licenses/pycp/COPYING
}

# vim:set ts=2 sw=2 et:
