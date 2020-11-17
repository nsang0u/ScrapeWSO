'''
For use by Williams Students with valid WSO login information. 

Noah Nsangou

'''
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

QUERY_STR = "A OR B OR C OR D OR E OR F OR G OR H OR I OR J OR K OR L OR M OR N OR P OR Q OR R OR S OR T OR U OR V OR W OR X OR Y OR Z"

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Arguments missing! \nUsage: python Selenium_scrapeWSO.py <username> <password> <output filename> \n")
        exit()
    my_unix = sys.argv[1]
    my_pwd = sys.argv[2]
    filename=sys.argv[3]

    driver = webdriver.Chrome() 
    
    # LOGIN
    login_url = "https://wso.williams.edu/account/login"
    driver.get(login_url)

    unix_input = driver.find_element_by_xpath("//*[@id='unixID']")
    pwd_input = driver.find_element_by_xpath("//*[@id='password']")

    unix_input.send_keys(my_unix)
    pwd_input.send_keys(my_pwd)
    pwd_input.send_keys(Keys.RETURN)

    
    # NAVIGATE TO FACEBOOK SEARCH
    cookies = driver.get_cookies()
    facebook_button = driver.find_element_by_xpath("//*[@id='nav-menu-content']/li[2]/a")
    facebook_button.click()

    
    # SUBMIT QUERY
    wait_success_search = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id='search']")))
    if wait_success_search:
        query_input = driver.find_element_by_xpath("//*[@id='search']")
    query_input.send_keys(QUERY_STR)
    query_input.send_keys(Keys.RETURN)

    
    # LOCATE 'NEXT' BUTTON
    try:
        wait_success_next_button = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id='root']/div/div/article/section/div/button[2]")))
    except TimeoutException:
        print("Next button wait failure")
        wait_success_next_button = False
        
    if wait_success_next_button:
        print("wait success")
        next_button = driver.find_element_by_xpath("//*[@id='root']/div/div/article/section/div/button[2]")
        next_button_enabled = not next_button.get_attribute("disabled") 
        print("START: next_button enabled: " + str(next_button_enabled))
        count = 1
    else:
        print("Next button not found")

        
    # DATA COLLECTION AND RESULT ITERATION LOOP
    datatable = pd.DataFrame()    
    while next_button_enabled:
        table_wait = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='root']/div/div/article/section/table")))

        pagenum_div = driver.find_element_by_xpath("//*[@id='root']/div/div/article/section/div")
        pagenum = int(pagenum_div.text.strip().split()[1])
        print("Page " + str(pagenum))
        
        try:
            table = driver.find_element_by_xpath("//*[@id='root']/div/div/article/section/table")
            tableHTML = table.get_attribute('outerHTML')
            newtable = pd.read_html(tableHTML)
            datatable = pd.concat([datatable, newtable[0]], sort=False)
        except NoSuchElementException:
            print("Table not found")
            break 

        try:
            next_button = driver.find_element_by_xpath("//*[@id='root']/div/div/article/section/div/button[2]")
            next_button_enabled = not next_button.get_attribute("disabled") 
        except NoSuchElementException:
            print("Next button not found")
            break
        
        if next_button_enabled:
            count += 1
            nextpagetext = "Page " + str(pagenum + 1)
            print("nextpagetext: " + nextpagetext)
            next_button.click()
            try:
                pagewait = WebDriverWait(driver, 10).until(EC.text_to_be_present_in_element((By.XPATH, "//*[@id='root']/div/div/article/section/div"), nextpagetext))
            except TimeoutException:
                print("Page change timeout")
                break
        else:
            print("End of results")

            
    #DATATABLE PREP AND EXPORT
    print("Collection done... preparing datatable")
    students = datatable.Name.str.contains("'*'\d{2} *$")
    student_datatable = datatable[students].drop(['Room/Office'], axis=1)
    student_datatable["Unix"] = student_datatable["Unix"].astype(str) + "@williams.edu"

    student_datatable.to_csv(filename, columns=["Name", "Unix"], index=False)

    print("Done!")
    driver.quit()
    print("Disconnect success")
