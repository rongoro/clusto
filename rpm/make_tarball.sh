#!/bin/bash

lasttag="$( git describe --tags --abbrev=0 )"
version=$( echo $lasttag | awk -F- '{ print $2 }' )
prefix="clusto-${version}"

echo "Appending prefix $prefix..."
git archive --format=tar --prefix=$prefix/ HEAD | gzip > ./$(git rev-parse --show-cdup)/rpm/clusto-$version.tar.gz
echo "Wrote clusto-$version.tar.gz"
