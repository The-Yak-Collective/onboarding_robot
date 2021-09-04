#!/usr/bin/env bash

YAK_LINKS="$1"

tail +2 "$1" \
	| sed -e 's/^.*", "//' \
	| sed -e 's/"$//' \
	| sed -e 's/; /\n/g' \
	| sed -e 's/\()\|),\|)\.\)$//' \
	| sed -e 's/?s=.*$//' \
	| cat -n \
	| sort -uk2 \
	| sort -n \
	| cut -f2- \
	| grep -E "https://(www\.)?twitter\.com/.*/status/.*"
	| sed -e 's/$/"/'
