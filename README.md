# ics2map
generate a MAP of many EVENT LOCATIONS from a given calendar events ICS file

## purpose: CO2 emissions reduction during hedonist summer
Given a long list of festival event calendar entries, all around Europe, 
this helps me to choose those festivals (that I like and)
which reduce the number of kilometers needed to drive there.

Your usage: Please share with us: [edit wiki](https://github.com/drandreaskrueger/ics2map/wiki/your-usages-of-this-repo)

## genesis
A broad search of (Psytrance, DnB, personal growth) festivals in Europe
resulted in more options than anyone person could enjoy in one summer. 
(a "Luxusproblem" in German, lol)

In a 2nd step, candidates were turned into calendar entries.
Exported as ICS file (Internet Calendaring and Scheduling Core Object Specification). 
Locations are stored in `LOCATION:...` lines.

With the **help of an AI** (see below), most of the code here was created.

## run creates outputs

    python makeMap.py

created at runtime:

    outputs/
      log.txt
      geocodeCache.csv
      geocodeFailed.csv
      map.html
      mapData.csv

## repo creation log
### venv in windows using python 3.14

    c:
    
    winget install 9NQ7512CXL7T # install Python install manager
    py install 3.14 # install Python 3.14
     
    cd C:\_DATA\CODE\_ECLIPSE-WS\_ENVS # venvs in my workspace
    
    py -3.14 -m venv ics2map
    ics2map\Scripts\activate.bat
    python.exe -m pip install --upgrade pip
    
    pip install ics geopy python-dateutil
    

### github repo
Choose LGPL2.1 license, Python .gitignore, etc.

    git config user.name "Andreas Krueger"
    git config user.email "find-my-repo@instead.of.using.this.fake.email"


### AI supported coding
See [AI-log.md](AI/README-AI.md) for the full conversation that created this code.




