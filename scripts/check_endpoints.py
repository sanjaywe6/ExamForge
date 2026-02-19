import urllib.request

urls = [
    'http://127.0.0.1:8000/exams/enter/',
    'http://127.0.0.1:8000/exams/student/',
    'http://127.0.0.1:8000/exams/',
]

for u in urls:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'check-script'})
        with urllib.request.urlopen(req, timeout=5) as r:
            data = r.read(1024)
            print(u, r.status)
            print(data.decode('utf-8', errors='replace')[:300])
            print('-' * 60)
    except Exception as e:
        print(u, 'ERROR', e)
