# selenium webdriver
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC    

import requests

from bs4 import BeautifulSoup

import time

# autofill models
from .models import Section, Question, Answer, Log

def check_form(id, url):

    section = Section.objects.get(id=id)
    questions = section.get_questions()

    # browser user agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'
    }

    page = requests.get(url, headers=headers)

    soup = BeautifulSoup(page.content, 'html.parser')

    # grab all the fields class
    fields = soup.find_all(class_='freebirdFormviewerComponentsQuestionBaseRoot')

    if questions.exists():
        for question in questions:
            answers = question.get_answers()
            for answer in answers:
                answer.delete()
            question.delete()

    # loop through all the field class and specify the question type
    for field in fields:
        
        teks = field.find(class_='freebirdFormviewerComponentsQuestionBaseTitle').text
        
        tanggal = field.find(class_='freebirdFormviewerComponentsQuestionDateLabel')
        waktu = field.find(class_='freebirdFormviewerComponentsQuestionTimeLabel')
        jawaban_singkat = field.find(class_='quantumWizTextinputPaperinputInput')
        paragraf = field.find(class_='quantumWizTextinputPapertextareaInput')
        radio = field.find_all(class_='appsMaterialWizToggleRadiogroupOffRadio')
        checkbox = field.find_all(class_='quantumWizTogglePapercheckboxInk')
        dropdown = field.find(class_='quantumWizMenuPaperselectOption')

        question = Question(
            section=section,
            text=teks
        )

        element_answers = []
        answer_type = ''
        
        if tanggal:
            question.type = 'Tanggal'
            answer_type += question.type
        elif waktu:
            question.type = 'Waktu'
            answer_type += question.type
        elif jawaban_singkat:
            placeholder = field.find(class_='quantumWizTextinputPaperinputPlaceholder')
            if placeholder:
                question.type = 'Jawaban Singkat'
                answer_type += question.type
        elif radio:
            pilihan_ganda = field.find(class_='docssharedWizToggleLabeledLabelWrapper')
            skala_linier = field.find_all(class_='freebirdMaterialScalecontentColumn')
            kisi_pilihan_ganda = field.find_all(class_='freebirdFormviewerComponentsQuestionGridCell')
            if pilihan_ganda:
                question.type = 'Pilihan Ganda'
                answer_type += question.type

                elements = field.find_all(class_='docssharedWizToggleLabeledLabelWrapper')

                for element in elements:
                    element_label = element.find(class_='docssharedWizToggleLabeledLabelText').text
                    element_answers.append(element_label)
            elif skala_linier:
                question.type = 'Skala Linier'
                answer_type += question.type

                for element in skala_linier:
                    element_label = element.find(class_='freebirdMaterialScalecontentLabel').text
                    element_answers.append(element_label)

            elif kisi_pilihan_ganda:
                question.type = 'Kisi Pilihan Ganda'
                answer_type += question.type
                row_elements = field.find_all(class_='appsMaterialWizToggleRadiogroupGroupContent')
                col_elements = field.find(class_='freebirdFormviewerComponentsQuestionGridColumnHeader')
                all_header = []
                all_columns = []
                for element in row_elements:
                    row_header = element.find(class_='freebirdFormviewerComponentsQuestionGridRowHeader').text
                    all_header.append(row_header)
                col = col_elements.find_all(class_='freebirdFormviewerComponentsQuestionGridCell')
                for c in col:
                    if c.text != '':
                        all_columns.append(c.text)

                for header in all_header:
                    for col in all_columns:
                        element_answers.append(f'{header},{col}')
        elif paragraf:
            question.type = 'Paragraf'
            answer_type += question.type
        elif checkbox:
            petak_kotak_centang = field.find_all(class_='freebirdFormviewerComponentsQuestionGridCell')
            if petak_kotak_centang:
                question.type = 'Petak Kotak Centang'
                answer_type += question.type

                row_elements = field.find_all(class_='freebirdFormviewerComponentsQuestionGridCheckboxGroup')
                col_elements = field.find(class_='freebirdFormviewerComponentsQuestionGridColumnHeader')
                all_header = []
                all_columns = []
                for element in row_elements:
                    row_header = element.find(class_='freebirdFormviewerComponentsQuestionGridRowHeader').text
                    all_header.append(row_header)
                col = col_elements.find_all(class_='freebirdFormviewerComponentsQuestionGridCell')
                for c in col:
                    if c.text != '':
                        all_columns.append(c.text)
                
                for header in all_header:
                    for col in all_columns:
                        element_answers.append(f'{header},{col}')
            else:
                question.type = 'Kotak Centang'
                answer_type += question.type
                elements = field.find_all(class_='docssharedWizToggleLabeledLabelWrapper')
                for element in elements:
                    element_title = element.find(class_='docssharedWizToggleLabeledLabelText').text
                    element_answers.append(element_title)
        elif dropdown:
            question.type = 'Drop Down'
            answer_type += question.type
            elements = field.find_all(class_='quantumWizMenuPaperselectContent')
            element_answers = []
            for element in elements:
                element_label = element.text
                element_answers.append(element_label)
        question.save()

        for el in element_answers:
            answer = Answer(
                question=question,
                text=el,
                type=answer_type
            )

            answer.save()

def submit_form(id):

    section = Section.objects.get(id=id)
    questions = section.question_set.all()

    PATH = "D:\Projects\Automatic Google Form Fill\src\chromedriver.exe"
    driver = webdriver.Chrome(PATH)

    driver.get(section.url)

    time.sleep(1)
    
    try:
        check = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "freebirdCommonViewProductnameLockupText"))
        )
        fields = driver.find_elements_by_class_name("freebirdFormviewerComponentsQuestionBaseRoot")
        for field in fields:
            field_question = field.find_element_by_class_name("freebirdFormviewerComponentsQuestionBaseTitle").text
            for question in questions:
                if question.text == field_question:
                    answers = Answer.objects.filter(question=question, correct=True)
                    if answers.exists():
                        for answer in answers:
                            if question.type == 'Jawaban Singkat':
                                element = field.find_element_by_class_name('quantumWizTextinputPaperinputInput')
                                element.send_keys(answer.text)
                            elif question.type == 'Paragraf':
                                element = field.find_element_by_class_name('quantumWizTextinputPapertextareaInput')
                                element.send_keys(answer.text)
                            elif question.type == 'Pilihan Ganda':
                                elements = field.find_elements_by_class_name('docssharedWizToggleLabeledLabelWrapper')
                                for element in elements:
                                    element_text = element.find_element_by_class_name("docssharedWizToggleLabeledLabelText").text
                                    if element_text == answer.text:
                                        element_radio = element.find_element_by_class_name("appsMaterialWizToggleRadiogroupOffRadio")
                                        element_radio.click()
                            elif question.type == 'Kotak Centang':
                                elements = field.find_elements_by_class_name('docssharedWizToggleLabeledLabelWrapper')
                                for element in elements:
                                    element_label = element.find_element_by_class_name('docssharedWizToggleLabeledLabelText').text
                                    if element_label == answer.text:
                                        element_checkbox = element.find_element_by_class_name('quantumWizTogglePapercheckboxInnerBox')
                                        element_checkbox.click()
                            elif question.type == 'Drop Down':
                                element = field.find_element_by_class_name('quantumWizMenuPaperselectOption')
                                element.send_keys(answer.text)
                            elif question.type == 'Skala Linier':
                                elements = field.find_elements_by_class_name('freebirdMaterialScalecontentColumn')
                                for element in elements:
                                    element_label = element.find_element_by_class_name('freebirdMaterialScalecontentLabel').text
                                    if element_label == answer.text:
                                        element_radio = element.find_element_by_class_name('appsMaterialWizToggleRadiogroupOffRadio')
                                        element_radio.click()
                            elif question.type == 'Kisi Pilihan Ganda':
                                column_row = field.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridColumnHeader')
                                row_elements = field.find_elements_by_class_name('appsMaterialWizToggleRadiogroupGroupContent')
                                column_elements = column_row.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCell')
                                column_list = [colel.text for colel in column_elements if colel.text != '']
                                row, col = answer.text.split(',')
                                for rowel in row_elements:
                                    rowel_title = rowel.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridRowHeader').text
                                    if rowel_title == row:
                                        rowel_choice = rowel.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCell')[column_list.index(col) + 1]
                                        rowel_radio = rowel_choice.find_element_by_class_name('appsMaterialWizToggleRadiogroupOffRadio')
                                        rowel_radio.click()
                            elif question.type == 'Petak Kotak Centang':
                                column_row = field.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridColumnHeader')
                                row_elements = field.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCheckboxGroup')
                                column_elements = column_row.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCell')
                                column_list = [colel.text for colel in column_elements if colel.text != '']
                                row, col = answer.text.split(',')
                                for rowel in row_elements:
                                    rowel_title = rowel.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridRowHeader').text
                                    if rowel_title == row:
                                        rowel_choice = rowel.find_elements_by_class_name('freebirdFormviewerComponentsQuestionGridCell')[column_list.index(col) + 1]
                                        rowel_radio = rowel_choice.find_element_by_class_name('freebirdFormviewerComponentsQuestionGridCheckbox')
                                        rowel_radio.click()
                            elif question.type == 'Tanggal':
                                element = field.find_element_by_class_name('quantumWizTextinputPaperinputInput')
                                element.send_keys(answer.text)
                            elif question.type == 'Waktu':
                                hour, minute = answer.text.split(':')
                                elements = field.find_elements_by_class_name('quantumWizTextinputPaperinputInput')
                                done_hour = False
                                for element in elements:
                                    if not done_hour:
                                        element.send_keys(hour)
                                        done_hour = True
                                    else:
                                        element.send_keys(minute)
                    else:
                        return ['Failed', f'Pertanyaan {question.text} belum memiliki jawaban, silahkan isi jawabannya terlebih dahulu']
        submit_button = driver.find_elements_by_class_name("appsMaterialWizButtonPaperbuttonContent")[-1]
        submit_button.click()

        log = Log(
            user=section.user,
            section=section,
            status='Success',
            message='Form berhasil dikirim'
        )
        log.save()

        time.sleep(2)
    finally:
        driver.quit()

    return ['Success', 'Form berhasil dikirim']

