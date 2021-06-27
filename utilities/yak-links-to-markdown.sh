#!/usr/bin/env bash

# Requires the following non-default Debian packages:
#
#     python3-bs4

YAK_LINKS="$1"

while read -r URL; do
	TITLE="$(python3 -c "import bs4, requests; print(bs4.BeautifulSoup(requests.get('$URL').text).title.text)" 2> /dev/null)"
	TITLE="$(echo "$TITLE" | sed -e '/^$/d')"
	TITLE="$(echo "$TITLE" | tr '\n' ' ')"
	TITLE="$(echo "$TITLE" | sed -e 's/ \+/ /g')"
	TITLE="$(echo "$TITLE" | sed -e 's/^\s\+//')"
	TITLE="$(echo "$TITLE" | sed -e 's/\s\+$//')"
	if [[ -n "$TITLE" ]] && [[ "$TITLE" != "403 Forbidden" ]] && [[ "$TITLE" != "Sorry! Something went wrong!" ]]; then
		echo "[$TITLE]($URL)  "
	fi
done < <(tail +2 "$1" \
        | sed -e 's/^.*", "//' \
        | sed -e 's/"$//' \
        | sed -e 's/; /\n/g' \
        | sed -e 's/(\([^()]\+\))/%28\1%29/g' \
        | sed -e 's/\()\|),\|)\.\)$//' \
        | sed -e 's/?\(l\|t\|s\|usp\|gclid\|twclid\|utm_source\|utm_medium\|utm_campaign\|pf_rd_r\|pf_rd_p\|pd_rd_r\|pd_rd_w\|pd_rd_wg\|ref_\|source\|psc\|ref\)=.*$//' \
        | sed -e '/https:\/\/discord\.com\//d' \
        | sed -e '/https:\/\/www\.notion\.so\//d' \
        | sed -e '/https:\/\/twitter\.com\//d' \
        | cat -n \
        | sort -uk2 \
        | sort -n \
        | cut -f2-)
