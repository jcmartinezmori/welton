#!/bin/bash
set -e

OTP_DIR="/Users/jcmartinezmori/Desktop/github/welton/output/otp"
OTP_JAR="$OTP_DIR/otp-shaded-2.8.1.jar"

wget "http://download.geofabrik.de/north-america/us/colorado-latest.osm.pbf" \
  -O "$OTP_DIR/colorado-latest.osm.pbf"

osmconvert "$OTP_DIR/colorado-latest.osm.pbf" \
  -b=-105.298,39.5037,-104.6474,40.1959 \
  --complete-ways \
  -o="$OTP_DIR/denver.pbf"

rm "$OTP_DIR/colorado-latest.osm.pbf"

java -Xmx2G -jar "$OTP_JAR" \
  --buildStreet \
  --save \
  "$OTP_DIR"