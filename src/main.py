from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import json



import time



        

class Website():
    def __init__(self, link, test_xpath):
        print("opening website")
        self.link = link

        options = webdriver.EdgeOptions()
        #options.add_argument('--headless')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--ignore-certificate-errors-spki-list')
        options.add_argument('--ignore-certificate-errors')
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
            time.sleep(scroll_pause_time)

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

    def urlToObjects(self, url):
        'this takes a course url and returns a Folder Object with the files and the subfolders'
        self.driver.get(url)
        elem = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//h1[@class='page-title']"))
        )
        table = self.driver.find_element(By.CSS_SELECTOR, "tbody")
        fields = table.find_elements(By.CLASS_NAME, "visible")

        folders = []
        files = []
        for field in fields:
            subfields = field.find_elements(By.CSS_SELECTOR, "td")
            
            
            
            if subfields[3].text.endswith("KB"): files.append(field)
            else: folders.append(field)

        thisDirectory = self.seleniumObjectsToMyDirectory(files, folders)
        thisDirectory.url = url

        return thisDirectory

    def seleniumObjectsToMyDirectory(self, files, folders):
        "Takes file and folders list in selenium format and returns one folder of our format fully populated"
        fileObjetcs = []
        
        for file in files:
            newFile = File()
            newFile.title, newFile.url, newFile.dateEdited = self.fileToData(file)
            fileObjetcs.append(newFile)
            
            
        
        
        subfolders = []
        for folder in folders:
            subfolder = Folder()
            subfolder.title, subfolder.url, subfolder.dateEdited = self.folderToData(folder)
            subfolders.append(subfolder)

        thisDirectory = Folder()
        thisDirectory.files = fileObjetcs
        thisDirectory.subfolders = subfolders
        
        return thisDirectory
            
    def folderToData(self, folderInstance):
        'Converts from folders found in the html to strings of the useful info'
        elements = folderInstance.find_elements(By.CSS_SELECTOR, "td")
        anchor = elements[2].find_element(By.CSS_SELECTOR, "a")
        url = anchor.get_attribute("href")
        title = anchor.get_attribute("title")
        dateAdded = elements[4].get_attribute("title")
        return title, url, dateAdded
    
    def fileToData(self,fileInstance):
        'Converts from files found in the html to strings of the useful info'
        elements = fileInstance.find_elements(By.CSS_SELECTOR, "td")
        anchor = elements[2].find_element(By.CSS_SELECTOR, "a")
        url = anchor.get_attribute("href")
        dateAdded = elements[4].get_attribute("title")
        title = anchor.get_attribute("title")
        
        return title, url, dateAdded




class File():
    def __int__(self):
        self.title = None
        self.url = None
        self.dateAdded = None
        self.dateEdited = None
        self.md5 = None
        self.directoryStored = None
        

        return
    
class Folder():
    def __init__(self):
        self.dateEdited = None
        self.title = None
        self.url = None
        self.directoryStored = None
        self.subfolders = None
        self.files = None

    def parse_directories(self, directories_to_be_parshed,site):
        new_directories_to_be_parshed = []
        for directory in directories_to_be_parshed:
            for subfolder in directory.subfolders:
                subfolder = site.urlToObjects(subfolder.url)
                new_directories_to_be_parshed.append(subfolder)

        self.parse_directories(new_directories_to_be_parshed)




            
        
        

    
        

    


                
        


        
        


class Course():
    def __init__(self, courseID, courseName, isFaivourite):
        self.courseID = courseID
        self.courseName = courseName
        downloadedFilesDirectoy = None

        
        self.courseHomeUrl = "https://eclass.upatras.gr/courses/" + self.courseID 
        self.courseFilesUrl = "https://eclass.upatras.gr/modules/document/?course=" + self.courseID 
        
        self.downloadedFilesDirectory = downloadedFilesDirectoy
        self.isFaivourite = isFaivourite
        





if __name__ == "__main__":
    
    username="up1107454"
    password="tracrouria"
    saveDirectory = "D:\\ECE\\personal\\python\\Eclass Downloader\\Downloaded Courses"
    
    test_xpath = "//a[@class='btn btn-default btn-login']"
    eclassHomeUrl = "https://eclass.upatras.gr/"

    downloadOnlyFaivourite = True

    

    
    
   
    courses = []
    
    # print(os.getcwd())
    # with open("settings.json", "a+") as settings:
    #     print(settings)
    #     settings.seek(0)
    #     settings = json.load(settings)
        
    #     if settings(username) : pass

    
    
    site = Website(eclassHomeUrl, test_xpath)
    site.login(username, password)
    #print(site.status())


    courses = site.find_all_courses()
    root_directory = site.urlToObjects(courses[0].courseFilesUrl)
    directories_to_be_parshed = [root_directory]
    

    

    

    
    print(root_directory)
    
    
        
    

    
                  
    site.driver.close()
    
    
    
