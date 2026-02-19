import urllib.request

BASE = 'http://127.0.0.1:8000'
PATHS = ['/login/student/', '/login/teacher/', '/login/college/']

for p in PATHS:
    url = BASE + p
    print('GET', url)
    try:
        resp = urllib.request.urlopen(url, timeout=5)
        body = resp.read(2048).decode('utf-8', errors='replace')
        status = resp.getcode()
        ok = 'OK' if status == 200 else f'STATUS {status}'
        found_heading = any(h in body for h in ['Student Login', 'Teacher Login', 'College Admin Login'])
        print(f'  {ok}; heading found: {found_heading}')
    except Exception as e:
        print('  ERROR:', repr(e))
