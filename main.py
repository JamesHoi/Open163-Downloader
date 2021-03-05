import requests
import json
import sys
import os
import threadpool
from urllib import parse
from common import download_file, _to_chinese4

def input_default(statement,default):
    text = input(statement)
    if text == "": text = str(default)
    return text


def get_url_query(url):
    result = parse.urlparse(url)
    query = parse.parse_qs(result.query)
    if "pid" not in query or "mid" not in query or result.netloc != 'open.163.com': return {}
    query["pid"] = query["pid"][0]
    query["mid"] = query["mid"][0]
    return query


def get_current_episode(data,pid):
    for index, video in enumerate(data["videoList"]):
        if video["plid"] == pid:
            return index


def download_video(video,path,quality,key,index,no_head):
    dic = {"Sd":"标清","Hd":"高清","Shd":"超清","Share":"标清（包含字幕）"}
    head = _to_chinese4(index+1)+"、" if not no_head else ""
    download_file(video[key],path,head+video["title"]+" - "+dic[quality]+".mp4")
    for sub in video["subList"]:
        filename = head+video["title"]+" - "+sub["subName"]+"字幕.srt"
        download_file(sub["subUrl"],path,filename)


def download_videos(data, episode, quality, path, max_workers):
    base_key = "mp4"+quality+"Url"
    if data["videoList"][episode[0]][base_key] == "": base_key += "Orign"
    pool = threadpool.ThreadPool(max_workers)

    # 新建线程池
    func_var = []
    for inx, video in enumerate(data["videoList"]):
        if inx in episode:func_var.append(([video, path, quality, base_key, inx, len(episode)==1], None))
    reqs = threadpool.makeRequests(download_video, func_var)
    [pool.putRequest(req) for req in reqs]
    pool.wait()
    print("已成功下载全部视频及字幕")


def main():
    # 获取输入
    print("软件介绍：")
    print("注意：软件为网易公开课下载器，并非网易云课堂！！")
    print("软件支持多线程，可分别下载视频及字幕，可选择画质(倘若原视频有)。支持分集下载")
    print("作者: JamesHoi")
    print("Github项目: https://github.com/JamesHoi/Open163-Downloader")
    print("")
    print("请输入视频页面链接下载")
    print("链接范例一：https://open.163.com/newview/movie/free?pid=MF750DHJV&mid=MF751IN70")
    print("链接范例二：https://open.163.com/newview/movie/free?pid=MA32VG4SA&mid=MA35IIC76")
    while True:
        input_url = input("请输入网易公开课视频链接或课程列表：")
        query = get_url_query(input_url)
        if "pid" in query:
            print("[正在获取数据，请等待]")
            print("")
            r = requests.get("https://c.open.163.com/open/mob/movie/list.do?plid=" + query["pid"])
            content = json.loads(r.content)
            data = content["data"]
            if content["code"] == 200: break
        print("请输入正确的链接，参考范例链接 https://open.163.com/newview/movie/free?pid=MA32VG4SA&mid=MA35IIC76")

    # 初始化下载选择
    course_name = data["title"]
    print("检测到视频为："+ course_name)
    video_num = len(data["videoList"])
    if video_num != 1: print("检测到一共有%s集" %video_num)
    print("[按Enter自动选择默认]")
    if video_num != 1: print("[支持分集下载，用逗号隔开，范例：1,3-9,12-15]")
    current_episode = get_current_episode(data, query["pid"])
    episode = input_default("下载第几集？(全部下载填all,当前视频填current) (默认:current):","current") if video_num != 1 else [0]
    if episode == "all": episode = range(video_num)
    elif episode == "current": episode = [current_episode]
    elif type(episode) == str:
        parts = episode.split(","); episode = []
        for part in parts:
            heads = part.split("-")
            if len(heads) ==2: episode.extend(list(range(int(heads[0])-1,int(heads[1]))))
            else: episode.append(int(heads[0])-1)
    max_worker = int(input_default("最多同时多少个视频一起下载(默认:5):",5)) if (video_num != 1 and episode != [current_episode]) else 1
    video_type = input_default("请选择影片格式 1.字幕与影片分开(某些影片不能分开字幕) 2.获取已合成字幕影片(只有标清) (默认:1):",1)
    if int(video_type) == 2: quality = "Share"
    else:
        notice = "检测到有画质 "; qualities = []; video = data["videoList"][current_episode-1]
        dic = {"Sd":"标清","Hd":"高清","Shd":"超清"}
        for key in dic:
            if video["mp4"+key+"Url"] != "" or video["mp4"+key+"UrlOrign"] != "":
                qualities.append(key)
        for index, quality in enumerate(qualities):
            notice += "%s.%s "%(index+1,dic[quality])
        index = input_default(notice+"请选择(默认:最高画质):",len(qualities))
        quality = qualities[int(index)-1]

    # 开始下载
    if episode == [0]: path = ""
    else:
        if not os.path.exists(course_name):
            os.mkdir(course_name)
        path = course_name + "/"
        with open(path + "课程介绍.txt", "wb+") as f:
            f.write(data["description"].encode())
    print("")
    print("[开始下载视频]")
    print("[若下载速度太快，可能会看不到下载信息]")
    download_videos(data, episode, quality, path, max_worker)
    os.system("pause")

if __name__ == '__main__':
    sys.exit(main())