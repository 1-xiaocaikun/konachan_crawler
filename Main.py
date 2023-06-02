import undetected_chromedriver as uc
from selenium.webdriver.remote.webdriver import By
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from dotenv import load_dotenv      # pip install python-dotenv
from loguru import logger
import datetime
import random
import json
import time
import csv
import os
import re

import Download_Images_



def check_floder(FloderName:str):
    """检查给的文件夹是否存在,不在的话路径(相对路径也行)上所有文件夹都会被创建"""
    if not os.path.isdir(FloderName):
        os.makedirs(FloderName)
        
def my_init(CurrentFile:str=__file__):
    """把 .env 文件里的信息汇总,以及选择是否为当前运行的py程序配置日志(默认给Main配置日志)"""
    load_dotenv(".env")
    page_s,page_e = int(os.getenv("START_PAGE")),int(os.getenv("END_PAGE"))
    start_page = min((page_s,page_e))
    end_page = max((page_s,page_e)) if abs(page_e-page_s)<10 else start_page+9
    img_floder_path,screen_shot_path,csv_path,log_path = \
        map(os.path.abspath,map(os.getenv,["IMG_FLODER_PATH",
                                           "SCREEN_SHOT_PATH",
                                           "CSV_PATH",
                                           "LOG_PATH"]))
    list(map(check_floder,[img_floder_path,screen_shot_path,csv_path,log_path]))

    my_name = os.path.basename(CurrentFile)
    log_name = os.path.splitext(my_name)[0]+'.log'
    absolute_log_file = f"{log_path}/{log_name}"
    if not os.path.exists(absolute_log_file):
        with open(file=absolute_log_file,mode='w',encoding='utf-8')as f:
            f.write("log文件不存在,由程序自动创建\n")
    logger.add(absolute_log_file)
    return [start_page,end_page,img_floder_path,screen_shot_path,csv_path]


def get_img_info_dict(MatchedStr:str)->dict:
    """
        作用是从正则匹配后的字符串中提取图片各种信息(图片地址、宽、高、上传者等),以dict(字典)返回;
    根据网站的写法,字典中包含了:"tags"、"file_url"、"file_size"、"jpeg_url"、"width"、"height"等信息

    输入:
        MatchedStr (str): 通过正则模板 r"Post\.register\({[^}]+}\)" 匹配出来的字符串（长这样"Post.register({...})"）
    
    返回:
        a dict: 包含图片所有信息的字典
    """
    return json.loads(MatchedStr[14:-1])

def add_FileType_to_DictList(InfoDictList:list, FileTypeList:list):
    """
        konachan.net的网页上大概包含四种图片:原图(png或者jpg),jpeg(用户上传时为jpg,或由png压缩),
    sample(jpeg压缩,预览图点开后的样例图),preview(预览图)
        通过该函数,给记录图片信息的dict添加 file_type 属性,记录原图是png还是jpg(不考虑体积,同分辨率下应该都更看重png吧?)

    输入:
        InfoDictList (list): 元素为dict,包含图片信息的list
        FileTypeList (list): 原图的类型,如['png','jpg','jpg']
    """
    for oneDictInList, file_type in zip(InfoDictList, FileTypeList):
        oneDictInList['file_type'] = file_type

def write_image_info_to_csv(ImageInfoList:list, CsvFile:str):
    """
        将需要的信息写入csv文件中,需要注意的是:网页的字典里面不含 file_type,要写入的话 ImageInfoList 必须经过
    add_FileType_to_DictList 处理
    """
    # 定义需要写入csv文件的字段名
    infoInCsv = ['id','tags', 'file_type', 'file_url','file_size', 'width', 'height',  'jpeg_url', 'sample_url', 'preview_url', 'source']
    
    with open(CsvFile, mode='w',encoding='utf_8_sig',newline='') as f:
        writer = csv.DictWriter(f, fieldnames=infoInCsv)

        # 只有当文件为空的时候才写入表头
        if f.tell() == 0:
            writer.writeheader()
        
        # 写入每个图片的信息
        for eachImgInfoDict in ImageInfoList:
            writer.writerow({key:eachImgInfoDict[key] for key in infoInCsv})

def my_process(PageStart:int,PageEnd:int,ScreenShotPath:str,ImgFloderPath:str,CsvFile:str):
    "这是我爬取图片的整个逻辑,你可以按F12检查网页,根据需求自己调整"
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--headless")   # 无头模式,注释掉这句话程序运行过程中会弹出chrome浏览器
    driver = uc.Chrome(version_main=113,options=chrome_options)     # 打开浏览器
    firstConnectURL = f"https://konachan.net/post?page={PageStart}&tags="
    driver.get(url=firstConnectURL)
    time.sleep(5+random.uniform(0.5,1))   # 5秒盾       
    logger.success("顺利通过检查,正在下载,请稍候...")
    RePattern = r"Post\.register\({[^}]+}\)"    # 正则表达式,在 "https://konachan.net/post?page={PageStart}&tags=" 类型网页的源码中匹配
    shouldDownload = 0      # 在 PageStart-PageEnd 中找到的所有图片链接数
    reallyDownload = 0      # 去掉文件夹中已经存在的,实际下载的图片数
    for i in range(PageStart,PageEnd+1):
        driver.get_screenshot_as_file(f"{ScreenShotPath}/page_{i}.png")     # 给当前页面截一张图
        pageSourse = driver.page_source
        MatchedStrInList = re.findall(RePattern, pageSourse)      # 非常好用的正则匹配(这意味着以前走了很多弯路┭┮﹏┭┮)
        shouldDownload += len(MatchedStrInList)
        ImgInfoList = list(map(get_img_info_dict,MatchedStrInList))  # 从网页源码中提取到的图片原始信息
        allFileTypeList = list(map(lambda InfoDict: InfoDict.get('file_url').split('.')[-1],ImgInfoList))    # 原始图片的类型('png'or'jpg')
        add_FileType_to_DictList(ImgInfoList,allFileTypeList)       # 在每个原始dict的基础上,加上file_type的信息
        write_image_info_to_csv(ImgInfoList,CsvFile)    # 把图片信息写入csv文件中,要写哪些属性在函数里修改
        
        # 准备下载图片需要的信息:图片的链接、图片的文件名
        imgURLList = []
        fileNameList = []
        for eachDict in ImgInfoList:
            imgURLList.append(eachDict.get('file_url'))
            fileNameList.append(f"{eachDict.get('id')}.{eachDict.get('file_type')}")
        # 函数会返回一个实际下载的图片数量(文件夹里已有的不会下载)
        downloadNums = Download_Images_.DownLoadImg(imgURLList,ImgFloderPath,fileNameList).download_images()
        
        reallyDownload+=downloadNums    # 实际下载的数量记一下
        
        # 最后一页前点击下一页并等待网页响应(如果下载2页,只需点一次)
        if i<PageEnd:
            # 参考 https://github.com/ultrafunkamsterdam/undetected-chromedriver/tree/master/example 82-88行
            driver.find_element(By.CLASS_NAME,"next_page").click_safe()
            WebDriverWait(driver, timeout=5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "next_page"))
            )
    driver.quit()   # 关闭浏览器
    return (shouldDownload,reallyDownload)


if __name__ == '__main__':
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime(f"%y-%m-%d_%H-%M-%S")
    Start_Page,End_Page,ImgFloderPath,ScreenShotPath,CsvPath = my_init()
    
    print(f"当前时间:{formatted_time}")
    datetime_in_screen_shot_path = f"{ScreenShotPath}/{formatted_time}"
    check_floder(datetime_in_screen_shot_path)
    
    start_time = time.time()
    PicNums,ReallyDownNums = \
        my_process(Start_Page,
                   End_Page,
                   ScreenShotPath=datetime_in_screen_shot_path,
                   ImgFloderPath=ImgFloderPath,
                   CsvFile=f"{CsvPath}/konachan.net_page-{Start_Page}-{End_Page}_{formatted_time}.csv")
    end_time = time.time()
    
    cost_time = end_time - start_time
    hour = int(cost_time//3600)
    mins = int(cost_time//60)
    secs = int(cost_time%60)
    
    logger.info(f"在{Start_Page}-{End_Page}页共找到:{PicNums}张图片,已存在:{PicNums-ReallyDownNums}张,实际下载:{ReallyDownNums}张,共耗时:{hour}时{mins}分{secs}秒")
    
    
    
    

