#!/bin/sh

mkdir -p tmp
./scripts/kconfig.pl '>' target/linux/generic/config-4.19 $1 > tmp/config-default_built
./scripts/kconfig.pl - tmp/config-default_built $2 > tmp/config-default.sub_defconfig
echo "$(grep -v "CONFIG_INITRAMFS_ROOT_GID" tmp/config-default.sub_defconfig)" > tmp/config-default.sub_defconfig
echo "$(grep -v "CONFIG_INITRAMFS_ROOT_UID" tmp/config-default.sub_defconfig)" > tmp/config-default.sub_defconfig
echo "$(grep -v "CONFIG_INITRAMFS_SOURCE" tmp/config-default.sub_defconfig)" > tmp/config-default.sub_defconfig
mv tmp/config-default.sub_defconfig $3
