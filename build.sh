set -v
git clone https://github.com/MikeMirzayanov/testlib.git
mkdir dist
cp ./{checker.py,hasher.py,main.py,server.py,__init__.py,settings.json} ./dist
sed -i "s|api_server|${API_SERVER}|" ./dist/settings.json
cat ./dist/settings.json
cp -a ./models ./dist
mkdir ./dist/checkers
cp ./testlib/testlib.h ./dist/checkers/
docker build -t deadsith/lightest-testing:latest -t deadsith/lightest-testing:$VERSION .
set +v