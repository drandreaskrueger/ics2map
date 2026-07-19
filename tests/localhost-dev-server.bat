echo OFF
echo .
echo . Careful: When new .js or .css, you might have to delete browser download cache.
echo .
cd ..
python -m http.server 8000
pause