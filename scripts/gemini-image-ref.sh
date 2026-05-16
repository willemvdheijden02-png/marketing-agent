#!/usr/bin/env bash
# gemini-image-ref.sh — Generate an image via Gemini 3 Pro Image Preview
#
# Usage:
#   ./gemini-image-ref.sh <prompt> <aspect_ratio> <output_path> [reference_image_path]
#
# aspect_ratio: "1:1" | "4:3" | "3:4" | "16:9" | "9:16"
# reference_image_path: pass "" or omit to skip
#
# Requires: GEMINI_API_KEY env var, perl (with MIME::Base64), curl
set -euo pipefail

PROMPT="${1:?Usage: gemini-image-ref.sh <prompt> <aspect_ratio> <output_path> [ref_image]}"
ASPECT_RATIO="${2:?aspect_ratio required (e.g. 1:1)}"
OUTPUT_PATH="${3:?output_path required}"
REFERENCE_IMAGE_PATH="${4:-}"

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
    echo "ERROR: GEMINI_API_KEY is not set." >&2
    exit 1
fi

MODEL="gemini-3-pro-image-preview"
API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${GEMINI_API_KEY}"

TMPDIR_LOCAL=$(mktemp -d)
PAYLOAD_FILE="${TMPDIR_LOCAL}/payload.json"
RESPONSE_FILE="${TMPDIR_LOCAL}/response.json"
cleanup() { rm -rf "${TMPDIR_LOCAL}"; }
trap cleanup EXIT

# ── Build JSON payload with perl ──────────────────────────────────────────────
perl - "${PROMPT}" "${ASPECT_RATIO}" "${REFERENCE_IMAGE_PATH}" "${PAYLOAD_FILE}" <<'PERL'
use strict;
use warnings;
use MIME::Base64 qw(encode_base64);

my ($prompt, $aspect, $ref_path, $out_file) = @ARGV;

# JSON-escape the prompt string
$prompt =~ s/\\/\\\\/g;
$prompt =~ s/"/\\"/g;
$prompt =~ s/\n/\\n/g;
$prompt =~ s/\r/\\r/g;
$prompt =~ s/\t/\\t/g;
$prompt =~ s/[\x00-\x08\x0b\x0c\x0e-\x1f]/sprintf("\\u%04x", ord($&))/ge;

# Start with the text part
my @parts = (qq({"text": "$prompt"}));

# Attach reference image if supplied
if ($ref_path && $ref_path ne "" && -f $ref_path) {
    open(my $fh, "<:raw", $ref_path) or die "Cannot open ref image '$ref_path': $!\n";
    local $/;
    my $raw = <$fh>;
    close($fh);

    my $b64 = encode_base64($raw, "");  # no line breaks

    my $mime = "image/jpeg";
    $mime = "image/png"  if $ref_path =~ /\.png$/i;
    $mime = "image/gif"  if $ref_path =~ /\.gif$/i;
    $mime = "image/webp" if $ref_path =~ /\.webp$/i;

    push @parts, qq({"inline_data":{"mime_type":"$mime","data":"$b64"}});
}

my $parts_json = join(",\n        ", @parts);

my $payload = qq({
  "contents": [
    {
      "parts": [
        $parts_json
      ]
    }
  ],
  "generationConfig": {
    "responseModalities": ["IMAGE"],
    "imageConfig": {
      "aspectRatio": "$aspect"
    }
  }
});

open(my $out, ">", $out_file) or die "Cannot write payload to '$out_file': $!\n";
print $out $payload;
close($out);
print STDERR "Payload written (${\(-s $out_file)} bytes)\n";
PERL

# ── POST to Gemini ────────────────────────────────────────────────────────────
HTTP_CODE=$(curl -s -w "%{http_code}" -o "${RESPONSE_FILE}" \
    -X POST "${API_URL}" \
    -H "Content-Type: application/json" \
    --data-binary "@${PAYLOAD_FILE}")

if [[ "${HTTP_CODE}" != "200" ]]; then
    echo "ERROR: Gemini API returned HTTP ${HTTP_CODE}" >&2
    cat "${RESPONSE_FILE}" >&2
    exit 1
fi

# ── Decode image from response ────────────────────────────────────────────────
perl - "${RESPONSE_FILE}" "${OUTPUT_PATH}" <<'PERL'
use strict;
use warnings;
use MIME::Base64 qw(decode_base64);

my ($resp_file, $out_path) = @ARGV;

open(my $fh, "<:raw", $resp_file) or die "Cannot read response: $!\n";
local $/;
my $json = <$fh>;
close($fh);

# Check for API-level error
if ($json =~ /"error"\s*:/) {
    print STDERR "API error in response:\n$json\n";
    exit 1;
}

# Extract the first base64 image blob from the response JSON
# Gemini returns: {"candidates":[{"content":{"parts":[{"inlineData":{"mimeType":"...","data":"..."}}]}}]}
if ($json =~ /"data"\s*:\s*"((?:[A-Za-z0-9+\/\n]|=)+)"/) {
    my $b64 = $1;
    $b64 =~ s/\s+//g;

    # Ensure output directory exists
    (my $dir = $out_path) =~ s|/[^/]+$||;
    mkdir $dir unless -d $dir;

    open(my $out, ">:raw", $out_path) or die "Cannot write '$out_path': $!\n";
    print $out decode_base64($b64);
    close($out);
    print "Saved: $out_path\n";
    exit 0;
}

print STDERR "No image data found in Gemini response.\n";
print STDERR "Response (truncated):\n", substr($json, 0, 800), "\n";
exit 1;
PERL
