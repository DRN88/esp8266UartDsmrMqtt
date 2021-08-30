# Micropython build environment

## Micropython esp-open-sdk build esp toolchain esp8266 espressif ubuntu 20.04

* https://docs.micropython.org/en/latest/develop/gettingstarted.html
* https://docs.espressif.com/projects/esp-idf/en/release-v3.0/get-started/linux-setup.html

* Ubuntu 20.04
* You'll need at least 5GB free space
* Build time approx: 30 mins with 4 cores i7-4770

### Get sources
```
git clone https://github.com/micropython/micropython
git clone --recursive https://github.com/pfalcon/esp-open-sdk
```

### Packages
```
sudo apt-get -y install python2 python2.7-dev make autoconf build-essential net-tools htop git wget gperf bison binutils-doc cpp-doc gcc-9-locales debian-keyring g++-multilib g++-9-multilib gcc-9-doc gcc-multilib libtool flex bison gdb gcc-doc gcc-9-multilib glibc-doc bzr libstdc++-9-doc texinfo help2man libtool libtool-bin libtool-doc libncurses-dev
```

### Apply diff to fix bash version check
```diff
--- crosstool-NG/configure.ac	2021-08-25 19:51:42.124229514 +0000
+++ crosstool-NG/configure.ac-good	2021-08-25 19:59:30.942518084 +0000
@@ -190,7 +190,7 @@
 AC_CACHE_CHECK([for bash >= 3.1], [ac_cv_path__BASH],
     [AC_PATH_PROGS_FEATURE_CHECK([_BASH], [bash],
         [[_BASH_ver=$($ac_path__BASH --version 2>&1 \
-                     |$EGREP '^GNU bash, version (3\.[1-9]|4)')
+                     |$EGREP '^GNU bash, version ([0-9\.]+)')
           test -n "$_BASH_ver" && ac_cv_path__BASH=$ac_path__BASH ac_path__BASH_found=:]],
         [AC_MSG_RESULT([no])
          AC_MSG_ERROR([could not find bash >= 3.1])])])
```

### remove --dry-run to patch
```
user@espbuilder:~/build/esp-open-sdk# patch --dry-run -p0 < bashfix.patch 
```

### fix missing "expat 2.1.0".
```
wget "https://sourceforge.net/projects/expat/files/expat/2.1.0/expat-2.1.0-RENAMED-VULNERABLE-PLEASE-USE-2.3.0-INSTEAD.tar.gz/download" -O "expat-2.1.0.tar.gz"

# extract it from "tar.gz"
tar -xzf "expat-2.1.0.tar.gz"

# rebuild archive but as "tar.xz"
tar -cJf expat-2.1.0.tar.xz expat-2.1.0

# copy the "expat-2.1.0.tar.xz" to the proper location
mkdir -p crosstool-NG/.build/tarballs/
cp expat-2.1.0.tar.xz crosstool-NG/.build/tarballs/

# You might need to clean up before re-running make
rm -Rfv crosstool-NG/.build/src/expat-2.1.0 crosstool-NG/.build/src/.expat-2.1.0.extracting
```

### temp swap Python to version 2
```
# https://github.com/pfalcon/esp-open-sdk/issues/339
cd /usr/bin/
sudo ln -sf python2 python
```

### Build it
```
make # -j4
```

### tail the build log
```
user1@espbuilder:~/esp-open-sdk$ tail -f crosstool-NG/build.log
```

### After successful build, swap it back to version 3
```
# https://github.com/pfalcon/esp-open-sdk/issues/339
cd /usr/bin/
sudo ln -sf python3 python
```


```
...

make[4]: Leaving directory '/home/user1/esp-open-sdk/lx106-hal'
make[3]: Leaving directory '/home/user1/esp-open-sdk/lx106-hal'
make[2]: Leaving directory '/home/user1/esp-open-sdk/lx106-hal'
make[1]: Leaving directory '/home/user1/esp-open-sdk/lx106-hal'

Xtensa toolchain is built, to use it:

export PATH=/home/user1/esp-open-sdk/xtensa-lx106-elf/bin:$PATH

Espressif ESP8266 SDK is installed, its libraries and headers are merged with the toolchain

user1@espbuilder:~/esp-open-sdk$ 
```
