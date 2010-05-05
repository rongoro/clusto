#!/bin/bash

lasttag="$( git describe --tags --abbrev=0 )"
version=$( echo $lasttag | awk -F- '{ print $2 }' )
prefix="clusto-${version}"

echo "Appending prefix $prefix..."
git archive --format=tar --prefix=$prefix/ $lasttag > ./$(git rev-parse --show-cdup)/clusto-$version.tar
tar -C $(dirname $0 ) --transform="s@clusto.spec@clusto-${version}/clusto.spec@" -rvf ./$(git rev-parse --show-cdup)/clusto-$version.tar clusto.spec
gzip ./$(git rev-parse --show-cdup)/clusto-$version.tar
echo "Wrote clusto-$version.tar.gz"
