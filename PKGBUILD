#Maintainer: "Yannick LM <yannicklm1337 AT gmail DOT com>"

pkgname=pycp
pkgver="6.1.2"
pkgrel=1
pkgdesc="cp and mv with a progressbar"
url="http://github.com/yannicklm/pycp"
arch=('any')
license=('MIT')
depends=('python2')
makedepends=('python2' 'help2man')
source=("http://pypi.python.org/packages/source/p/pycp/pycp-${pkgver}.tar.gz")
md5sums=('6f370ea0d19fbc495c00a9c8d0973e7a')

conflicts=('pycp-git')

build() {
  cd ${srcdir}/pycp-${pkgver}
  python2 setup.py build
}

package() {
  cd ${srcdir}/pycp-${pkgver}
  python2 setup.py install --root=$pkgdir/ --optimize=1
  mkdir -p $pkgdir/usr/share/licenses/pycp
  install COPYING.txt $pkgdir/usr/share/licenses/pycp/COPYING
}

# vim:set ts=2 sw=2 et:
