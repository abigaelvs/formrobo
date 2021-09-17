# selenium webdriver
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC    

import requests

from bs4 import BeautifulSoup

from datetime import datetime
import time

# autofill models
from .models import Section, Question, Log

# browser user agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
}

def get_fields(url: str):
    """Get all of the Google Form fields"""
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.content, "html.parser")
    fields = soup.find_all(class_='freebirdFormviewerComponentsQuestionBaseRoot')

    return fields


def check_form(url: str) -> dict:
    """
        1. Scrape link that user input to the formulir form
        2. Grab all the field class
        3. Loop trough all the fields and specify the question type
        5. Get the field question
        6. Save all the question and answers in dictionary
    """

    fields = get_fields(url)

    result = {}

    qclass = {
        "TextInput": "quantumWizTextinputPaperinputInput",
        "Waktu": "freebirdFormviewerComponentsQuestionTimeLabel",
        "Tanggal": "freebirdFormviewerComponentsQuestionDateLabel",
        "Paragraf": "quantumWizTextinputPapertextareaInput",
        "Radio": "appsMaterialWizToggleRadiogroupOffRadio",
        
        "PilihanGanda": {
            "elements": "docssharedWizToggleLabeledLabelWrapper",
            "label": "docssharedWizToggleLabeledLabelText"
        },
        "KisiPilihanGanda": {
            "main_class": "appsMaterialWizToggleRadiogroupGroupContent",
            "row_col": "freebirdFormviewerComponentsQuestionGridColumnHeader",
            "col": "freebirdFormviewerComponentsQuestionGridCell",
            "header": "freebirdFormviewerComponentsQuestionGridRowHeader"
        },
        "SkalaLinier": {
            "elements": "freebirdMaterialScalecontentColumn",
            "label": "freebirdMaterialScalecontentLabel"
        },
        "KotakCentang": {
            "main_class": "quantumWizTogglePapercheckboxInk",
            "elements": "docssharedWizToggleLabeledLabelWrapper",
            "label": "docssharedWizToggleLabeledLabelText"
        },
        "PetakKotakCentang": {
            "main_class": "freebirdFormviewerComponentsQuestionGridCell",
            "row_el": "freebirdFormviewerComponentsQuestionGridCheckboxGroup",
            "row_header": "freebirdFormviewerComponentsQuestionGridRowHeader",
            "col_el": "freebirdFormviewerComponentsQuestionGridColumnHeader",
        },
        "DropDown": "quantumWizMenuPaperselectContent"
    }

    for f in fields:
        teks = f.find(class_='freebirdFormviewerComponentsQuestionBaseTitle').text
        textinput = f.find(class_=qclass["TextInput"])
        paragraf = f.find(class_=qclass["Paragraf"])
        radio = f.find(class_=qclass["Radio"])
        checkbox = f.find(class_=qclass["KotakCentang"]["main_class"])
        dropdown = f.find(class_=qclass["DropDown"])

        if textinput:
            waktu = f.find(class_=qclass["Waktu"])
            tanggal = f.find(class_=qclass["Tanggal"])

            if waktu:
                result[teks] = {"question_type": "Waktu"}
            elif tanggal:
                result[teks] = {"question_type": "Tanggal"}
            else:
                result[teks] = {"question_type": "JawabanSingkat"}

            # set the choice type
            result[teks]["choice_type"] = "SingleElement"

        elif paragraf:
            result[teks] = {"question_type": "Paragraf", "choice_type": "SingleElement"}

        elif radio:
            pilihanganda = f.find_all(class_=qclass["PilihanGanda"]["elements"])
            skalalinier = f.find_all(class_=qclass["SkalaLinier"]["elements"])
            kisipilihanganda = f.find_all(class_=qclass["KisiPilihanGanda"]["main_class"])

            if pilihanganda:
                result[teks] = {"question_type": "PilihanGanda", "answers": []}

                for el in pilihanganda:
                    label = el.find(class_=qclass["PilihanGanda"]["label"]).text
                    result[teks]["answers"].append(label)

            elif skalalinier:
                result[teks] = {"question_type": "SkalaLinier", "answers": []}

                for el in skalalinier:
                    label = el.find(class_=qclass["SkalaLinier"]["label"]).text
                    result[teks]["answers"].append(label)

            elif kisipilihanganda:
                result[teks] = {"question_type": "KisiPilihanGanda", "answers": {"row": [], "col": []}}
                row_col = f.find(class_=qclass["KisiPilihanGanda"]["row_col"])
                col = row_col.find_all(class_=qclass["KisiPilihanGanda"]["col"])[1:]

                for r in kisipilihanganda:
                    header = r.find(class_=qclass["KisiPilihanGanda"]["header"]).text
                    result[teks]["answers"]["row"].append(header)

                for c in col:
                    result[teks]["answers"]["col"].append(c.text)

            # set the choice type
            result[teks]["choice_type"] = "MultipleElement"

        elif checkbox:
            petakkotakcentang = f.find_all(class_=qclass["PetakKotakCentang"]["main_class"])
            
            if petakkotakcentang:
                result[teks] = {"question_type": "PetakKotakCentang", "answers": {"row": [], "col": []}}
                row_el = f.find_all(class_=qclass["PetakKotakCentang"]["row_el"])
                col_el = f.find(class_=qclass["PetakKotakCentang"]["col_el"])
                
                for r in row_el:
                    header = r.find(class_=qclass["PetakKotakCentang"]["row_header"]).text
                    result[teks]["answers"]["row"].append(header)
                
                for c in col_el.find_all(class_=qclass["PetakKotakCentang"]["main_class"])[1:]:
                    result[teks]["answers"]["col"].append(c.text)
            else:
                result[teks] = {"question_type": "KotakCentang", "answers": []}
                elements = f.find_all(class_=qclass["KotakCentang"]["elements"])
                for el in elements:
                    el_title = el.find(class_=qclass["KotakCentang"]["label"]).text
                    result[teks]["answers"].append(el_title)
            
            # set the choice type
            result[teks]["choice_type"] = "MultipleElement"
        
        elif dropdown:
            result[teks] = {"question_type": "DropDown", "choice_type": "SingleElement", "answers": []}
            elements = f.find_all(class_=qclass["DropDown"])
            for el in elements:
                result[teks]["answers"].append(el.text)

    return result 


def submit_form(id: int):

    qclass = {
        "JawabanSingkat": "quantumWizTextinputPaperinputInput",
        "Paragraf": "quantumWizTextinputPapertextareaInput",
        "Waktu": "freebirdFormviewerComponentsQuestionTimeTimeInputs",
        "Tanggal": "quantumWizTextinputPaperinputInput",
        "SkalaLinier": {
            "main_class": "freebirdMaterialScalecontentColumn",
            "sub_class": "appsMaterialWizToggleRadiogroupOffRadio",
            "label": "freebirdMaterialScalecontentLabel"
        },
        "PilihanGanda": {
            "main_class": "docssharedWizToggleLabeledLabelWrapper",
            "sub_class": "appsMaterialWizToggleRadiogroupOffRadio",
            "label": "docssharedWizToggleLabeledLabelText"
        },
        "KotakCentang": {
            "main_class": "docssharedWizToggleLabeledLabelWrapper",
            "sub_class": "quantumWizTogglePapercheckboxInnerBox",
            "label": "docssharedWizToggleLabeledLabelText"
        },
        "KisiPilihanGanda": {
            "row_elements": "appsMaterialWizToggleRadiogroupGroupContent",
            "input": "appsMaterialWizToggleRadiogroupOffRadio"
        },
        "PetakKotakCentang": {
            "row_elements": "freebirdFormviewerComponentsQuestionGridCheckboxGroup",
            "input": "freebirdFormviewerComponentsQuestionGridCheckbox"
        },
        "DropDown": "quantumWizMenuPaperselectOption"
    }
    
    section = Section.objects.get(id=id)
    questions = Question.objects.get_question_dict(id)

    PATH = "D:\Projects\Automatic Google Form Fill\src\chromedriver.exe"
    driver = webdriver.Chrome(PATH)

    driver.get(section.url)

    time.sleep(1)

    try:
        check = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "freebirdCommonViewProductnameLockupText"))
        )

        fields = driver.find_elements_by_class_name("freebirdFormviewerComponentsQuestionBaseRoot")
        for f in fields:
            f_question = f.find_element_by_class_name("freebirdFormviewerComponentsQuestionBaseTitle").text
            if questions.get(f_question):
                # not yet created
                answers = questions[f_question]["answers"]
                question_type = questions[f_question]["question_type"]
                choice_type = questions[f_question]["choice_type"]

                if choice_type == "SingleElement":

                    if question_type == "Tanggal":
                        if answers[0] == "Now":
                            answers[0] = datetime.now().strftime("%m/%d/%Y")

                    if question_type == "Waktu":
                        elements = f.find_element_by_class_name("freebirdFormviewerComponentsQuestionTimeTimeInputs")
                        timeedit = elements.find_elements_by_class_name("freebirdFormviewerComponentsQuestionTimeNumberEdit")
                        hour, minute = answers[0].split(":")
                        el_idx = 0
                        for h in [hour, minute]:
                            fill = timeedit[el_idx].find_element_by_class_name("quantumWizTextinputPaperinputInput")
                            fill.send_keys(h)
                            el_idx += 1
        
                    else:                
                        el = f.find_element_by_class_name(qclass[question_type])
                        el.send_keys(answers[0])
                            
                elif choice_type == "MultipleElement":

                    if question_type == "KisiPilihanGanda" or question_type == "PetakKotakCentang":
                        
                        # previous name is column row
                        header = f.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridColumnHeader')

                        # previous name is column_elements
                        header_elements = header.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCell')
                        
                        row_elements = f.find_elements_by_class_name(qclass[question_type]["row_elements"])
                        column_list = [h.text for h in header_elements if h.text != '']

                        for a in answers:
                            row, col = a.split(",")

                            for r in row_elements:
                                title = r.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridRowHeader').text
                                if title == row:
                                    choice = r.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCell')[column_list.index(col) + 1]
                                    rowel_radio = choice.find_element_by_class_name(qclass[question_type]["input"])
                                    rowel_radio.click()
                   
                    else:
                        elements = f.find_elements_by_class_name(qclass[question_type]["main_class"])
                        for el in elements:
                            el_text = el.find_element_by_class_name(qclass[question_type]["label"]).text
                            answer = (el_text if el_text in answers else None)
                            if answer:
                                choice = el.find_element_by_class_name(qclass[question_type]["sub_class"])
                                choice.click()

        submit_button = driver.find_elements_by_class_name("appsMaterialWizButtonPaperbuttonContent")[-1]
        submit_button.click()
        

        Log.objects.add_log({
            "user": section.user,
            "section": section,
            "status": "Success",
            "message": "Form successfully submitted"
        })

        time.sleep(2)

    except Exception as e:
        return e

    finally:
        driver.quit()

    return questions