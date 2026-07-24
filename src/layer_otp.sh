#!/bin/bash
set -e

OTP_DIR="/Users/jcmartinezmori/Desktop/github/welton/output/otp"
OTP_JAR="$OTP_DIR/otp-shaded-2.8.1.jar"

java -Xmx2G -jar "$OTP_JAR" \
  --loadStreet \
  --save \
  "$OTP_DIR"

java -Xmx2G -jar "$OTP_JAR" \
  --load \
  "$OTP_DIR"
