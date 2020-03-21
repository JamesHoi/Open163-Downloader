import requests
import time

def downloadFile(url,path, name):
    r = requests.get(url, stream=True,verify=False)
    length = float(r.headers['content-length'])
    f = open(path+name, 'wb')
    count = 0
    count_tmp = 0
    time1 = time.time()
    for chunk in r.iter_content(chunk_size=512):
        if chunk:
            f.write(chunk)
            count += len(chunk)
            if time.time() - time1 > 2:
                p = count / length * 100
                speed = (count - count_tmp) / 1024 / 1024 / 2
                count_tmp = count
                print(name + ': ' + formatFloat(p) + '%' + ' Speed: ' + formatFloat(speed) + 'M/S')
                time1 = time.time()
    f.close()

def formatFloat(num):
    return '{:.2f}'.format(num)