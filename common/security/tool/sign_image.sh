#!/bin/bash

function usage() {
	echo "sign_image.sh ${PLATFORM} ${PRODUCT}"
	echo "e.g. sign_image.sh mt6880 evb6880v1_datacard"
}

function sign() {
	echo python ${TOOL_PATH}/sign_flow.py "${PLATFORM}" "${PRODUCT}"
	PYTHONDONTWRITEBYTECODE=True PRODUCT_OUT=${PRODUCT_OUT} BOARD_AVB_ENABLE= python ${TOOL_PATH}/sign_flow.py -env_cfg ${TOOL_PATH}/env.cfg "${PLATFORM}" "${PRODUCT}"
}

if [ "$1" == "" ]; then
	usage;
	exit 1
fi
PLATFORM=$1

if [ "$2" == "" ]; then
	usage;
	exit 0
fi
PRODUCT=$2

TOOL_PATH=mtk/tools/common/security/tool
CONFIG_PATH=mtk/tools/common/security/config
PRODUCT_OUT=openwrt/bin/targets/${PLATFORM}/${PRODUCT}

sign
