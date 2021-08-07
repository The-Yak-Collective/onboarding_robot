#!/usr/bin/env bash

# Requires the following non-default Debian packages:
#
#     python3-bs4

# Parse command line.
#
HELP="no"
if [[ $# -eq 2 ]]; then
	CMD="$1"
	FILE="$2"
else
	HELP="yes"
fi

# Make sure command line actually makes sense.
#
if [[ "$HELP" == "no" ]]; then
	case "$CMD" in
		markdown|html|html1|html2)
			if [[ ! -f "$FILE" ]]; then
				HELP="yes"
			fi
			;;
		*)
			HELP="yes"
			;;
	esac
fi

# Display help, if needed.
#
if [[ "$HELP" == "yes" ]]; then
	echo "USAGE: $(basename "$0") <markdown|html> <FILE>"
	echo ""
	echo "<markdown|html> - Required parameter; output link list in Markdown or"
	echo "                  HTML format. Note that Discord, Notion, and Twitter"
	echo "                  require JavaScript to extract any useful information,"
	echo "                  which is incompatible with the current scraping"
	echo "                  method. These links will be output as comments only."
	echo ""
	echo "<FILE> - A link text file of the sort produced by the \$links command."
	echo ""
	exit 1
fi

if [[ "$CMD" == "html" ]]; then
	echo "The 'html' output format is still experimental. Use 'html1' or 'html2'"
	echo "instead to see the current options."
	exit 1
fi

# Clean up FILE, storing it as LINK_DATA. Mostly this is about removing
# tracking tags, sorting URL parameters, and making sure that the
# protocol/domain is lower-cased. We also determine a direct channel
# link and compact the provided date/time string here.
#
# Final data structure:
#
#     channel|channel_url|timestamp|message_url|domain|link
#
LINK_DATA=""
while read -r LINE; do
	CHANNEL="$(echo "$LINE" | sed -e 's/^"\(.*\)", "\(.*\)", "\(.*\)", "\(.*\)"/\1/')"
	TIMESTAMP="$(echo "$LINE" | sed -e 's/^"\(.*\)", "\(.*\)", "\(.*\)", "\(.*\)"/\2/')"
	MESSAGE_URL="$(echo "$LINE" | sed -e 's/^"\(.*\)", "\(.*\)", "\(.*\)", "\(.*\)"/\3/')"
	LINKS="$(echo "$LINE" | sed -e 's/^"\(.*\)", "\(.*\)", "\(.*\)", "\(.*\)"/\4/')"

	CHANNEL_URL="$(echo "$MESSAGE_URL" | sed -e 's#/[0-9]\+$##')"

	TIMESTAMP="$(echo "$TIMESTAMP" | tr -d '\-\ :.')"

	# Sometimes multiple links are captured on a single line,
	# separated by "; ". We break this up and loop over these.
	#
	LINKS="$(echo "$LINKS" | sed -e 's/; /;/g' | tr ';' '\n')"

	for LINK in $LINKS; do
		# Borked parenthesis are a frequent thing we need to
		# fix.
		#
		LINK="$(echo "$LINK" | sed -e 's/(\([^()]\+\))/%28\1%29/g')"
		LINK="$(echo "$LINK" | sed -e 's/).\?$//')"

		# Extract link domain.
		#
		DOMAIN="$(echo "$LINK" | sed -e 's#^[^/]\+://##;s#/.*##')"

		# Break link into base + opts.
		#
		LINK_BASE="$(echo "$LINK" | sed -e 's/?.*//')"
		LINK_OPTS="$(echo "$LINK" | sed -e 's/.*?//' | tr '&' '\n' | sed -e 's/%20/ /g;s/^ \+//;s/ \+$//;s/ /%20/')"

		# If LINK_OPTS exists, strip known tracking tags and
		# normalize the tag order.
		#
		if [[ "$LINK_BASE" != "$LINK_OPTS" ]]; then
			OPT_DATA=""
			for OPT in $LINK_OPTS; do
				OPT_NAME="$(echo "$OPT" | sed -e 's/=.*//')"
				if [[ "$OPT_NAME" != "gclid" ]] \
					&& [[ "$OPT_NAME" != "l" ]] \
					&& [[ "$OPT_NAME" != "pd_rd_r" ]] \
					&& [[ "$OPT_NAME" != "pd_rd_w" ]] \
					&& [[ "$OPT_NAME" != "pd_rd_wg" ]] \
					&& [[ "$OPT_NAME" != "pf_rd_p" ]] \
					&& [[ "$OPT_NAME" != "pf_rd_r" ]] \
					&& [[ "$OPT_NAME" != "psc" ]] \
					&& [[ "$OPT_NAME" != "ref" ]] \
					&& [[ "$OPT_NAME" != "ref_" ]] \
					&& [[ "$OPT_NAME" != "s" ]] \
					&& [[ "$OPT_NAME" != "source" ]] \
					&& [[ "$OPT_NAME" != "t" ]] \
					&& [[ "$OPT_NAME" != "twclid" ]] \
					&& [[ "$OPT_NAME" != "usp" ]] \
					&& [[ "$OPT_NAME" != "utm_campaign" ]] \
					&& [[ "$OPT_NAME" != "utm_medium" ]] \
					&& [[ "$OPT_NAME" != "utm_source" ]]; then
						OPT_DATA="$(echo -e "$OPT_DATA\n$OPT")"
				fi
			done
			OPT_DATA="$(echo "$OPT_DATA" | sed -e '/^$/d' | sort -u)"
			if [[ -n "$OPT_DATA" ]]; then
				LINK="$LINK_BASE?"
				for OPT in $OPT_DATA; do
					LINK="$LINK$OPT&"
				done
				LINK="$(echo "$LINK" | sed -e 's/&$//')"
			else
				LINK="$LINK_BASE"
			fi
		fi

		LINK_DATA="$(echo -e "$LINK_DATA\n$CHANNEL|$CHANNEL_URL|$TIMESTAMP|$MESSAGE_URL|$DOMAIN|$LINK")"
	done
done < <(tail +2 "$FILE")

# Sort and de-duplicate LINK_DATA.
#
LINK_DATA="$(echo "$LINK_DATA" | sed -e '/^$/d' | sort -u)"

# Opening HTML boilerplate (for testing).
#
if [[ "$CMD" == "html1" ]] || [[ "$CMD" == "html2" ]]; then
	echo "<html>"
	echo "	<head>"
	echo "		<title>Test Document: $CMD</title>"
	echo "		<style>"
	echo "			a {"
	echo "				text-decoration: none;"
	echo "				color: orange;"
	echo "			}"
	echo "			a:hover,"
	echo "			a:active {"
	echo "				text-decoration: underline;"
	echo "			}"
	echo "		</style>"
	echo "	</head>"
	echo "	<body>"

fi

# Loop over link data and extract URL titles. If a title cannot be
# extracted, the page fails to load, or we're deailing with a domain
# known to misbehave (currently: internal links, Notion pages, and
# tweets), then we include it as an HTML comment instead (on the theory
# that someone might want to manually look up some/all of these).
#
CURRENT_CHANNEL=""
for LINK_DATUM in $LINK_DATA; do
	CHANNEL="$(echo "$LINK_DATUM" | sed -e 's/^\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)/\1/')"
	CHANNEL_URL="$(echo "$LINK_DATUM" | sed -e 's/^\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)/\2/')"
	TIMESTAMP="$(echo "$LINK_DATUM" | sed -e 's/^\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)/\3/')"
	MESSAGE_URL="$(echo "$LINK_DATUM" | sed -e 's/^\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)/\4/')"
	DOMAIN="$(echo "$LINK_DATUM" | sed -e 's/^\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)/\5/')"
	LINK="$(echo "$LINK_DATUM" | sed -e 's/^\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)|\(.*\)/\6/')"

	# Output current channel.
	#
	# FIXME: Right now we still get a channel header even if all
	# of the links are bad. Not sure how to fix this without
	# reimplementing this in a language that understands key/value
	# hashes.
	#
	if [[ "$CURRENT_CHANNEL" != "$CHANNEL" ]]; then
		if [[ "$CMD" == "markdown" ]]; then
			if [[ -n "$CURRENT_CHANNEL" ]]; then
				echo ""
			fi
			echo "#### [#$CHANNEL]($CHANNEL_URL)"
			echo ""
		elif [[ "$CMD" == "html" ]]; then
			echo "???" # TODO
		elif [[ "$CMD" == "html1" ]]; then
			echo "<h4><a href=\"$CHANNEL_URL\">#$CHANNEL</a></h4>"
		elif [[ "$CMD" == "html2" ]]; then
			if [[ -n "$CURRENT_CHANNEL" ]]; then
				echo "</ul>"
			fi
			echo "<strong><a href=\"$CHANNEL_URL\">#$CHANNEL</a></strong>"
			echo "<ul>"
		fi
		CURRENT_CHANNEL="$CHANNEL"
	fi

	if [[ "$DOMAIN" == "discord.com" ]] || [[ "$DOMAIN" == "www.notion.so" ]] || [[ "$DOMAIN" == "twitter.com" ]]; then
		TITLE=""
	else
		# Use Python 'request' module to get raw HTML, and then
		# extract the page title using BeautifulSoup.
		#
		TITLE="$(python3 -c "import bs4, requests; print(bs4.BeautifulSoup(requests.get('$LINK').text).title.text)" 2> /dev/null)"

		# Try to clean up multi-line titles and
		# extra/trailing/weird whitespace.
		#
		TITLE="$(echo "$TITLE" | sed -e '/^$/d')"
		TITLE="$(echo "$TITLE" | tr '\n' ' ')"
		TITLE="$(echo "$TITLE" | sed -e 's/\s\+/ /g')"
		TITLE="$(echo "$TITLE" | sed -e 's/^\s\+//')"
		TITLE="$(echo "$TITLE" | sed -e 's/\s\+$//')"
	fi

	# Output link based on the format specified by CMD.
	#
	if [[ -n "$TITLE" ]] && [[ "$TITLE" != "403 Forbidden" ]] && [[ "$TITLE" != "Sorry! Something went wrong!" ]]; then
		if [[ "$CMD" == "markdown" ]]; then
			echo "[🧵]($MESSAGE_URL) [$TITLE]($LINK)  "
		elif [[ "$CMD" == "html" ]]; then
			echo "???" # TODO
		elif [[ "$CMD" == "html1" ]]; then
			echo "<small><small><a href=\"$MESSAGE_URL\">&#x1f9f5;</a></small></small> <a href=\"$LINK\">$TITLE</a><br>"
		elif [[ "$CMD" == "html2" ]]; then
			echo "<li><a href=\"$LINK\">$TITLE</a>&nbsp;<small><small><a href=\"$MESSAGE_URL\">&#x1f9f5;</a></small></small></li>"
		fi
	else
		echo "<!-- $MESSAGE_URL :: $LINK -->"
	fi
done

# Closing HTML boilerplate (for testing).
#
if [[ "$CMD" == "html1" ]] || [[ "$CMD" == "html2" ]]; then
	if [[ "$CMD" == "html2" ]]; then
		echo "		</ul>"
	fi
	echo "	</body>"
	echo "</html>"
fi
