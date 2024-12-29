from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import json
import copy



#import time
from time import sleep
from datetime import datetime

from pathlib import Path



        

class Website():
    def __init__(self, link, test_xpath):
        print("opening website")
        self.link = link

        options = webdriver.EdgeOptions()
        #options.add_argument('--headless')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-certificate-errors')
        options.add_experimental_option("prefs", {
            "plugins.always_open_pdf_externally": True
        })
        self.driver = webdriver.Edge(options=options)
        self.driver.get(self.link)

        initialized = False
        while(initialized != True):
            try:
               elem = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, test_xpath)) )
               initialized = True
            
            except Exception as e:
                print(f"Object not located in initialization of website\n {e}")
        
    def status(self):
        login_xpath = "//a[@class='btn btn-default btn-login']"
        mainPage_xpath = "//h2[contains(text(),'Τα μαθήματα μου')]"
        initialized = False
        while(initialized != True):
            try:
               elem = WebDriverWait(self.driver, 5).until(
               EC.presence_of_element_located((By.XPATH, login_xpath)) )
               initialized = True
               return "Login_page"
            
            except:
                try:
                    elem = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, mainPage_xpath)) )
                    initialized = True
                    return "MainPage"
            
                except:
                    print("Status could not be found, retrying")

    def login(self, username, password):
        self.driver.find_element(By.XPATH, "//a[@class='btn btn-default btn-login']").click() #clock on login button

        #waiting for the email element to load
        elem = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='inputEmail']"))
        )


        #giving credentials
        elem.send_keys(username)
        elem = self.driver.find_element(By.XPATH, "//input[@id='inputPassword']")
        elem.send_keys(password)

        elem.send_keys(Keys.RETURN)
 
    def scroll(self):
        print("scrolling")
        body = self.driver.find_element(By.TAG_NAME, 'body')
        scroll_pause_time = 0.1
        scroll_strokes = 400

        for i in range(scroll_strokes):
            # Send arrow down
            body.send_keys(Keys.ARROW_DOWN)
            # Wait to load page
            sleep(scroll_pause_time) #time.sleep

    def find_all_courses(self):
        "This is supposed to scrape the eclass website and find all the courses that the user has subscribed"
        
        totalCoursesCountContainer = self.driver.find_element(By.XPATH, "//div[@id='portfolio_lessons_info']") 
        
        totalCoursesCountContainer = totalCoursesCountContainer.text.split()
        totalCoursesCount = totalCoursesCountContainer[5]
        print(f"Total courses that the user is enlisted in is: {totalCoursesCount}")

        coursesParsed = []
        while (len(coursesParsed)<int(totalCoursesCount)):
            unparshedCourses = self.driver.find_elements(By.CSS_SELECTOR, "table > tbody > tr")
            
            for course in unparshedCourses:
                left = course.find_element(By.CSS_SELECTOR, "td > strong > a")
                name = left.accessible_name
                url = left.get_attribute('href')
                id = url.split('/')[-2]
                
                right = course.find_element(By.CSS_SELECTOR, "td > a")
                faivourite = right.get_attribute('href').split('=')[-1]
                if faivourite == '0': faivourite = True
                else : faivourite = False
                coursesParsed.append(Course(id, name, faivourite ))
                
                
                if len(coursesParsed)%5 == 0: #going to the next page to view the rest courses
                    self.driver.find_element(By.XPATH, "//a[@id='portfolio_lessons_next']").click()

        return coursesParsed

    def urlToObjects(self, url, targetFolderObject):
        'this takes a course url and appends the attributes to the specified folder object including the files and the subfolders'
        self.driver.get(url)
        elem = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='page-title']"))
        )

        #title
        titlePanel = self.driver.find_elements(By.CLASS_NAME, "panel")
        title = titlePanel[0].text
        title.strip()
        title = title.replace("\n"," » ")
        titlePath = title.split(sep=" » ")   #this could be useful
        
        title = titlePath[-1]
        title = title.strip()
        
        
        


        #urls of files and subfolders
        table = self.driver.find_element(By.CSS_SELECTOR, "tbody")
        fields = table.find_elements(By.CLASS_NAME, "visible")

        folders = []
        files = []
        for field in fields:
            subfields = field.find_elements(By.CSS_SELECTOR, "td")
            typeSubfield = subfields[1]
            type = typeSubfield.find_element(By.CSS_SELECTOR, "span")
            type = type.get_attribute("class")
            #print(type)
            
            
            if type == "fa fa-folder":
                folders.append(field)
            else: #this is for folders
                files.append(field)


        

        self.seleniumObjectsToMyDirectory(files, folders, targetFolderObject)

        targetFolderObject.setUrl(url)
        targetFolderObject.setTitle(title)
        
    def seleniumObjectsToMyDirectory(self, files, folders, targetFolderObject): #used in UrlToObjects
        "Takes file and folders list in selenium format and returns one folder of our format fully populated"
        fileObjetcs = []
        
        for file in files:
            newFile = File()
            newFile.title, newFile.url, newFile.dateEdited = self.fileToData(file)
            fileObjetcs.append(newFile)
            
            
        
        
        subfolders = []
        for folder in folders:
            subfolder = Folder()
            subfolder.title, subfolder.url, subfolder.dateAdded = self.folderToData(folder)
            subfolders.append(subfolder)

        targetFolderObject.setFiles(fileObjetcs)
        targetFolderObject.setSubfolders(subfolders)
                 
    def folderToData(self, folderInstance): #used in seleniumObjetcsToMyDirectory which is used in UrlToObjetcs
        'Converts from folders found in the html to strings of the useful info'
        elements = folderInstance.find_elements(By.CSS_SELECTOR, "td")
        anchor = elements[2].find_element(By.CSS_SELECTOR, "a")
        url = anchor.get_attribute("href")
        title = anchor.text
        dateAdded = elements[4].text
        return title, url, dateAdded
    
    def fileToData(self,fileInstance):#used in seleniumObjetcsToMyDirectory which is used in UrlToObjetcs
        'Converts from files found in the html to strings of the useful info'
        elements = fileInstance.find_elements(By.CSS_SELECTOR, "td")
        anchor = elements[2].find_element(By.CSS_SELECTOR, "a")
        url = anchor.get_attribute("href")
        dateAdded = elements[4].get_attribute("title")
        title = anchor.get_attribute("title")
        
        
        return title, url, dateAdded
    
    def getCourseFolder(self, courseObject):
        'Makes sure that the current url in the files url of the given course'
        if (self.driver.current_url in courseObject.courseFilesUrl) or (self.driver.current_url in courseObject.courseHomeUrl):
            pass
        else:
            self.driver.get(courseObject.courseFilesUrl)

    def getCourseTitle(self, courseObject):
        'Returns the title string of the given course object (not the title of the folder)'
        self.getCourseFolder(courseObject)
        elem = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='page-title']"))
        )
        
        return elem.text

    def downloadFile(self, url):
        self.driver.get(r"https://eclass.upatras.gr/modules/document/file.php/EE1140/%CE%91%CF%80%CE%BF%CF%84%CE%B5%CE%BB%CE%AD%CF%83%CE%BC%CE%B1%CF%84%CE%B1%20%CE%95%CF%81%CE%B3%CE%B1%CF%83%CF%84%CE%B7%CF%81%CE%AF%CE%BF%CF%85/%CE%91%CE%A0%CE%9F%CE%A4%CE%95%CE%9B%CE%95%CE%A3%CE%9C%CE%91%CE%A4%CE%91/%CE%91%CF%80%CE%BF%CF%84%CE%B5%CE%BB%CE%AD%CF%83%CE%BC%CE%B1%CF%84%CE%B1/2022-2023/results_2022_2023.pdf")
        print("file downloaded")





class File():
    def __int__(self):
        self.title = "" 
        self.url = ""
        self.dateAdded = ""         #NOT populated yet | ismeant to be the date the file was originally detected
        self.dateEdited = ""        #the date eclass provides for the file (last day modified by teacher)
        self.md5 = ""               #NOT populated yet | meant to help with file version logging (the idea is to save old versions)
        self.directoryStored = ""   #NOT populated yet
        

        return
    
class Folder():
    def __init__(self):
        self.dateAdded = "" #NOT implemented | the day eclass provides as the date of the folder (the date the folder was made public)
        
        self.title = ""
        self.url = ""
        self.directoryStored = "" #NOT implemented
        self.subfolders = []
        self.files = []
        
    def __str__(self):
        
        self.printDirectory(0)
        
        return "finished"

    def printDirectory(self,depth):
        tab = "\t"
        for file in self.files:
            print(f"{tab*depth}{file.title}", end=" FILE\n")
        for folder in self.subfolders:
            print(f"{tab*depth}{folder.title}", end=" FOLDER\n")
            depth = depth+1
            folder.printDirectory(depth)
            depth = depth -1

    def parse_directories(self, site):
        #new_directories_to_be_parshed = []
        #for directory in directories_to_be_parshed:        

        for subfolder in self.subfolders:
            
            site.urlToObjects(subfolder.url, subfolder)
            
            if subfolder.url: 
                subfolder.parse_directories(site)
  
    def setUrl(self, url):
        self.url = url

    def setTitle(self,title):
        self.title = title

    def setFiles(self,files):
        self.files = files

    def setSubfolders(self, subfolders):
        self.subfolders = subfolders

    def addSubfolder(self, newfolder):     
        self.subfolders.append(newfolder)
        

class Course():
    def __init__(self, courseID, courseName, isFaivourite):
        self.courseID = courseID
        self.courseName = courseName
        downloadedFilesDirectoy = None

        
        self.courseHomeUrl = "https://eclass.upatras.gr/courses/" + self.courseID 
        self.courseFilesUrl = "https://eclass.upatras.gr/modules/document/?course=" + self.courseID 
        
        self.downloadedFilesDirectory = downloadedFilesDirectoy
        self.isFaivourite = isFaivourite
        

class Snapshot():
    def __init__(self, folderInstance, savepath, name):
        "take a snapshot, compare the differences with saved and merge"
        self.newFolder = dict()
        self.oldFolder = dict()
        self.savePath = savepath
    
        snapshotName = name

        try:                                                                       
            with open(self.savePath+"/"+snapshotName, "r", encoding='utf-8') as snapshot: #old snapshot exists 
                self.oldFolder = self.loadSavedSnapshot(snapshot)
                

        except FileNotFoundError:                                       #old snapshot doesnt exist: create and save
            with open(self.savePath+"/"+snapshotName, "w+", encoding='utf-8') as snapshot:     
                self.newFolder = self.createSnapshot(copy.deepcopy(folderInstance))
                self.saveSnapshot(self.newFolder, snapshot)
                
            
            

        except Exception as e:                                          #make a little prayer this doesn't happed
            print("something went really shit please fix this line 311 unknown error", e) 
        
    @staticmethod
    def testSnapshot(savePath, snapshotName):
        "returns true if snapshot exists and false if it doesnt"
        try:                                                                       
            with open(savePath+"/"+snapshotName, "r", encoding='utf-8') as snapshot: #old snapshot exists 
                return True
                
        except FileNotFoundError:                                       #old snapshot doesnt exist
            return False

    def createSnapshot(self, folder):
        'basically converts from Folder Object to dicttionary/json'
        folderDictionary = folder.__dict__
        self.fixSubfolders(folderDictionary)
        return folderDictionary
    
    def fixSubfolders(self, folderDictionary):
        
        #files
        shitFiles = folderDictionary["files"]
        folderDictionary["files"] = dict()#emptying the useless objects
        for shitFile in shitFiles:
            folderDictionary['files'][shitFile.title] = shitFile.__dict__ #readding the file in a good format

        #folders
        shitSubfolders = folderDictionary["subfolders"]
        folderDictionary["subfolders"] = dict() #emptying the subfolders field in order to replace the File objects with strings that can be jsoned
        for shitsubfolder in  shitSubfolders:
            folderDictionary['subfolders'][shitsubfolder.title] = shitsubfolder.__dict__ #rectify the inner subfolders 
        
        
        #fixing the inner folders as well
        subFolders = folderDictionary["subfolders"]
        if(subFolders):
            for subfolder in subFolders:
                self.fixSubfolders(subFolders[subfolder])
    
    def saveSnapshot(self, snapshotDictionary, fileStream):
        json.dump(snapshotDictionary,fileStream, indent=4)
        
    def loadSavedSnapshot(self, fileStream):
        "this function shouldreturn a Dictionary with the contents of a snapshot taken in the past in order to avoid parshing the eclass every time the program runs and waiting 10 minutes"
        return json.load(fileStream)
        
    def compare(self):
        "compares old instance with new and asks user for merging options"
        pass
    
#TODO recreate folder structure in given path
class DirectoryManager():
    def __init__(self, rootSaveDirectory):
        self.rootDirectory = rootSaveDirectory

    def verifySnapshot(self, snapshot): 
        'gets a snapshot and looks at the rootDirectory in order to verify that EVERY file and folder of the Snapshot are downloaded'
        
        
        pass

    def verifyFile(self, theoreticalMD5, filePath):
        'takes a path, calculates the files md5 and compares it to the theoretical MD5, returns true if they match'
        pass
    
    

    
        









if __name__ == "__main__":
    
    
    username="up1107454"
    password=""  #TODO find a way to get the password in a safe way from the user (Cookie? idk look it up requesting plaintext password is creepy)
    saveDirectory = "D:\\ECE\\personal\\python\\Eclass Downloader\\Downloads"
    snapshotDirectory = "D:/ECE/personal/python/Eclass Downloader/Snapshots"
    
    test_xpath = "//a[@class='btn btn-default btn-login']"
    eclassHomeUrl = "https://eclass.upatras.gr/"

    downloadOnlyFaivourite = True

    

    
    now = datetime.now()
    dt_string = now.strftime("%d-%m-%Y")
    snapshotName = f"{dt_string} snapshot"

    snapshotTest = Snapshot.testSnapshot(snapshotDirectory, snapshotName)
    root_directory = Folder()
    root_directory.setTitle("root directory")

    if snapshotTest == False:

   


        courses = []
        
        site = Website(eclassHomeUrl, test_xpath)
        site.login(username, password)
        #print(site.status())
    
    
        courses = site.find_all_courses()
        
        for course in courses:
            courseFolder = Folder()
            site.urlToObjects(course.courseFilesUrl, courseFolder)
            courseFolder.setTitle(site.getCourseTitle(course))
            courseFolder.parse_directories(site)
            root_directory.addSubfolder(courseFolder)
        
    
        snapshotInstance = Snapshot(root_directory, snapshotDirectory, snapshotName)
        site.driver.close()

    else:
        snapshotInstance = Snapshot(root_directory, snapshotDirectory, snapshotName)
        with open("snapshot.json", "w", encoding="utf-8") as file: json.dump(snapshotInstance.oldFolder, file, ensure_ascii=False, indent=4)
        
        site = Website(eclassHomeUrl, test_xpath)
        site.login(username, password)
        newSite = Website(eclassHomeUrl, test_xpath)
        newSite.downloadFile("dummyURL")
        downloadDirectory = DirectoryManager(saveDirectory)
        downloadDirectory.installSnapshot(snapshotInstance)

    
#TODO populate the newly created folders with their cooresponding files and log everything somewhere
    
#TODO create the log
#the log must contain:
#                       date added
#                       date modified by teacher
#                       md5 hash 
#                       filename
#                       is currently visible in eclass
#                       last date visible in eclass
#                           
#        print(root_directory)
        
                      
        
        
        
        
    