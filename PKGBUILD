pkgname=cranetexteditor
pkgver=0.1
pkgrel=1
pkgdesc="CRANE Text Editor – multi-mode terminal editor with mouse, media support"
arch=('any')
url="https://github.com/you/crane"
license=('MIT')
depends=('python' 'python-pygments' 'python-pillow' 'python-pygame' 'python-numpy')
source=('crane.py' 'cranelaunch'='crane' )
md5sums=('SKIP' 'SKIP')

package() {
  install -Dm755 crane "$pkgdir/usr/bin/crane"
  install -Dm755 crane.py "$pkgdir/usr/bin/crane.py"
}
