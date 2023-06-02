from loguru import logger
import threading
import requests
import random
import time
import os

import Main

class DownLoadImg():
    def __init__(self,ImgURLList:list,ImgFloderPath:str,FileNameList:list):
        # ImgURLList 应与 FileNameList 的长度相等
        self.write_lock = threading.Lock()
        self.ImgURLList = ImgURLList
        self.ImgFloderPath = ImgFloderPath
        self.FileNameList = FileNameList
        
    def save_OneImg_from_URL(self,OneImgURL:str,FloderPath_And_FileName:str):
        attemptTimes = 3
        for i in range(attemptTimes):
            try:
                response = requests.get(OneImgURL)
                if response.status_code == 200:
                    break
                elif response.status_code == 403:
                    logger.warning("403 Forbidden --> 寄,被服务器盯上了!")
            except requests.exceptions.HTTPError:
                if i < attemptTimes - 1:
                    logger.debug(f"蒙头睡{i+1}觉,期待奇迹的发生")
                    time.sleep(random.uniform(1,3))
                else:
                    logger.error(f"睡不过{attemptTimes},一直躺着是解决不了问题的!")
        if response.status_code == 200:
            self.write_ImgData_to_floder(response.content,FloderPath_And_FileName)
        elif response.status_code == 404:
            logger.debug(f"看看图片链接是不是有问题:{OneImgURL}")

    def write_ImgData_to_floder(self,ImgData:bytes,FloferPath_And_FileName:str):
        with self.write_lock:       # 多线程写入同一个文件夹时加锁
            try:
                with open(FloferPath_And_FileName,"wb")as f:
                    f.write(ImgData)
                    logger.success("图片写入成功!")
            except Exception as e:
                logger.error(f"图片{FloferPath_And_FileName}写入失败")
                print("失败原因:\n",e)
                time.sleep(2)
                # raise e

    def download_images(self):
        notRepetImgURLList = []
        notRepetFileNameList = []
        picURLNum = len(self.ImgURLList)    # 传进来的图片链接数
        repeatNum = 0           # 文件夹内重复存在的图片数量
        shouldDownNum = 0       # 实际应该下载的图片数量(不含重复)
        for eachURL,eachFileName in zip(self.ImgURLList,self.FileNameList):
            file = f"{self.ImgFloderPath}/{eachFileName}"
            if os.path.exists(file):
                logger.info(f"文件\"{file}\"已存在,不会重复下载")
                repeatNum += 1
                continue
            shouldDownNum += 1
            notRepetImgURLList.append(eachURL)
            notRepetFileNameList.append(file)
        logger.info(f"本次提供图片链接:{picURLNum}个,发现文件夹中已存在:{repeatNum}张,实际应从网页下载:{shouldDownNum}张")
        
        start_time = time.time()
        allThreads = [] # 创建线程列表
        if shouldDownNum > 0:
            logger.info("正在下载...")
            for eachURL,eachFileName in zip(notRepetImgURLList,notRepetFileNameList):
                # 创建并启动线程
                oneThread = threading.Thread(target=self.save_OneImg_from_URL, args=(eachURL,eachFileName))
                oneThread.start()
                allThreads.append(oneThread)
            # 等待所有线程完成
            for eachThread in allThreads:
                eachThread.join()
            end_time = time.time()
            time_cost = end_time-start_time
            logger.info(f"{shouldDownNum}张图片的下载任务已结束,耗时:{time_cost:.2f}s")
        return shouldDownNum
    
if __name__ == '__main__':
    # __file__ 是当前py文件的绝对路径(本文件 Download_Images_.py),
    # 可以在此处单独测试下载图片的函数或测试图片链接是否有问题,并把信息记录到日志里
    StartPage,EndPage,ImgFloderPath,ScreenShotPath,CsvPath = Main.my_init(__file__)
    logger.success(f"当前运行的程序:{__file__}")
    logger.info(f"{StartPage} --> {EndPage}")
    logger.info(f"{ImgFloderPath} | {ScreenShotPath} | {CsvPath}")