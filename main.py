#coding:utf-8
from selenium import webdriver
from downloader import downloadFile
import sys,os,threadpool

def program_dir():
    if hasattr(sys, 'frozen'):
        dir = sys._MEIPASS + "/"
    else:
        dir = "D:/WorkSpace/Python/Open163-Downloader/"
    return dir

def inputDefault(statement,default):
    text = input(statement)
    if text == "": text = str(default)
    return text

def gen_driver():
    opt = webdriver.ChromeOptions()
    opt.add_argument('--disable-gpu')
    opt.add_argument("--headless")
    opt.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=opt, executable_path=program_dir()+'Resource/chromedriver.exe')
    return driver

def getOldVersion(url):
    html = url.split("%2F")[3]
    return "http://open.163.com/special/sp/%s"%html

def getVideoPage(driver,url):
    driver.get(url)
    driver.implicitly_wait(5)
    video_url = driver.find_element_by_class_name("u-even").find_element_by_tag_name("a").get_attribute("href")
    return video_url

def getCourseName(driver):
    return driver.find_element_by_class_name("t-container__linkhover").text

def getPageUrl(driver):
    return driver.find_element_by_tag_name("video").get_attribute("src")

def seeMore(driver):
    u_seemore = driver.find_elements_by_class_name("u-seemore")
    if len(u_seemore):u_seemore[0].click()

def getVideoLength(driver):
    return driver.execute_script("return __NUXT__.state.movie.moiveList.length;")

def getVideoName(driver,episode):
    return driver.execute_script("return __NUXT__.state.movie.moiveList[%s].title"%episode)

def getVideoUrl(driver,episode,quality,orign=""):
    return driver.execute_script("return __NUXT__.state.movie.moiveList[%s].mp4%sUrl%s"%(episode,quality,orign))

def getVideoSrt(driver,episode):
    subTitles = {}
    subLength = driver.execute_script("return __NUXT__.state.movie.moiveList[%s].subList.length"%episode)
    for i in range(subLength):
        subName = driver.execute_script("return __NUXT__.state.movie.moiveList[%s].subList[%s].subName"%(episode,i))
        subUrl = driver.execute_script("return __NUXT__.state.movie.moiveList[%s].subList[%s].subUrl"%(episode,i))
        subTitles.update({subName:subUrl})
    return subTitles

def getVideoQualities(driver,orign=""):
    qualities = ["Sd", "Hd", "Shd", "Share"]
    list_del = []
    for i in range(len(qualities)):
        url = getVideoUrl(driver, 0, qualities[i],orign=orign)
        if url == "": list_del.append(qualities[i])
    for name in list_del: del qualities[qualities.index(name)]
    if len(qualities) == 1: [qualities,orign] = getVideoQualities(driver,orign="Orign")
    return [qualities,orign]

def getAllVideos(driver,quality,iscurrent=False,orign=""):
    videos = []
    for i in range(getVideoLength(driver)):
        if iscurrent: head_text = ""
        else: head_text = "[第%s集]" %(i+1)
        videos.append({"name":head_text+getVideoName(driver,i),"url":getVideoUrl(driver,i,quality,orign=orign),"srt":getVideoSrt(driver,i)})
    return videos

def downloadVideo(video,path,quality):
    dic = {"Sd":"标清","Hd":"高清","Shd":"超清","Share":"标清（包含字幕）"}
    downloadFile(video["url"],path,video["name"]+" - "+dic[quality]+".mp4")
    for subname,url in video["srt"].items():
        downloadFile(url,path,video["name"]+" - "+subname+"字幕.srt")

def downloadVideos(driver,episode,quality,orign,max_worker):
    # 初始化下载
    if episode == "origin":path = ""
    else:
        course_name = getCourseName(driver)
        print("课程: %s"%course_name)
        if not os.path.exists(course_name):
            os.mkdir(course_name)
        path = course_name + "/"
    print("[若下载速度太快，可能会看不到下载信息]")
    pool = threadpool.ThreadPool(max_worker)

    # 寻找下载链接进行匹配
    if episode == "origin":
        index = 0
        qualities = getVideoQualities(driver)[0]
        for qual in qualities:
            videos = getAllVideos(driver,qual,iscurrent=True,orign=orign)
            for inx, video in enumerate(videos):
                if video["url"] == getPageUrl(driver):
                    index = inx
                    break
            else: continue
            break
        videos = getAllVideos(driver, quality,iscurrent=True,orign=orign)
        video = videos[index]
        downloadVideo(video, path, quality)
    else:
        videos = getAllVideos(driver,quality,orign=orign)
        if episode == "all":
            func_var = []
            [func_var.append(([video,path,quality],None)) for video in videos]
            requests = threadpool.makeRequests(downloadVideo,func_var)
            [pool.putRequest(req) for req in requests]
        else:
            video = videos[int(episode)-1]
            downloadVideo(video,path,quality)
    pool.wait()
    print("已成功下载全部视频及字幕")

def chooseQuality(driver):
    [qualities,orign] = getVideoQualities(driver)
    del qualities[qualities.index("Share")]
    if len(qualities) != 1:
        notice = "检测到有画质 "
        dic = {"Sd":"标清","Hd":"高清","Shd":"超清"}
        for index, quality in enumerate(qualities):
            notice += "%s.%s "%(index+1,dic[quality])
        index = inputDefault(notice+"请选择(默认:最高画质):",len(qualities)-1)
    else: index = 1
    return [qualities[int(index)-1],orign]

def main():
    # 获取输入
    print("软件介绍：")
    print("注意：软件为网易公开课下载器，并非网易云课堂！！")
    print("软件支持多线程，可分别下载视频及字幕，可选择画质(倘若原视频有)")
    print("作者: JamesHoi")
    print("Github项目: https://github.com/JamesHoi/Open163-Downloader")
    print("")
    print("链接范例：")
    print("可输入课程链接下载，范例：")
    print("http://open.163.com/newview/movie/courseintro?newurl=%2Fspecial%2Fcuvocw%2Fputaojiuwenhua.html&1447983787771")
    print("可输入旧版课程链接，范例：http://open.163.com/special/sp/singlevariablecalculus.html")
    print("可输入视频页面下载，范例：http://open.163.com/newview/movie/free?pid=MF750DHJV&mid=MF751IN70")
    print("")
    input_url = input("请输入网易公开课视频链接或课程列表：")
    print("按Enter自动选择默认")
    max_worker = inputDefault("最多同时多少个视频一起下载(默认:5):",5)
    video_type = inputDefault("请选择影片格式 1.字幕与影片分开(某些影片不能分开字幕) 2.获取已合成字幕影片(只有标清) (默认:1):",1)

    # 初始化网页
    website = input_url.split("/")[3]
    type = input_url.split("/")[5].split("?")[0]
    driver = gen_driver()
    if type == "free": [videopage,default] = [input_url,{"name":"当前页面","value":"origin"}]
    elif type == "courseintro": [videopage,default] = [getVideoPage(driver,getOldVersion(input_url)),{"name":"下载全部","value":"all"}]
    elif website == "special": [videopage,default] = [getVideoPage(driver,input_url),{"name":"下载全部","value":"all"}]
    else:
        print("无法识别链接网页，无法下载")
        os.system("pause")
        sys.exit(0)

    # 询问下载
    driver.get(videopage)
    if getVideoLength(driver) == 1: episode = "origin"
    else: episode = inputDefault("下载第几集？(全部下载填all,当前页面填origin) (默认:%s):" % default["name"], default["value"])
    if video_type == "1":[quality,orign] = chooseQuality(driver)
    else: quality = "Share"

    # 开始下载
    try:
        downloadVideos(driver,episode,quality,orign,int(max_worker))
    finally:
        driver.quit()
        os.system("pause")

if __name__ == '__main__':
    sys.exit(main())