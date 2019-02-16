DATE="$(date -u +%FT%T)"
set -v
git clone https://github.com/MikeMirzayanov/testlib.git
mkdir dist
cp -R ./src/* ./dist
sed -i "s|api_server|${API_SERVER}|" ./dist/settings.json
cat ./dist/settings.json
mkdir ./dist/checkers
cp ./testlib/testlib.h ./dist/checkers/
docker build \
--build-arg version=$VERSION \
--build-arg vcs_ref=$TRAVIS_COMMIT \
--build-arg build_date=$DATE \
-t deadsith/lightest-testing:latest -t deadsith/lightest-testing:$VERSION .
set +v