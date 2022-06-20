from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import requests
import csv
import re


URL = 'https://spb.hh.ru/search/vacancy'
HEADERS = {'User-Agent':UserAgent().chrome,'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'}
MAX_PAGE = 100
currConv = False


def get_content(url, key_word, mp):
    params = {
        'text': key_word,
        'no_magic':'true',
        'items_on_page': str(20),
        'page': '1'
    }
    max_page = get_max_page(get_html(url, params), mp)
    vacancy = []
    for page in range(1,max_page):
        print(f"Получение страницы {page} из {max_page}...")
        params['page'] = str(page)
        vacancy += get_vacancy(get_html(url, params))
    return vacancy

def get_max_page(html, mp):
    soup = BeautifulSoup(html,'html.parser')
    button_page = soup.find_all('span', class_='pager-item-not-in-short-range')
    if button_page:
        max_page = int(button_page[-1].get_text())
        if (max_page > mp):
            return mp
        else:
            return max_page
    else:
        return 1

def get_vacancy(html):
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('div', class_= 'vacancy-serp-item')
    vacancies = []
    for table in tables:
        title = table.find('a', class_= 'bloko-link')
        price = table.find('span', class_= 'bloko-header-section-3')
        guc = table.find('div', class_='g-user-content')
        country = table.find('div', class_= 'bloko-text bloko-text_no-top-indent')
        company = table.find('a', class_= 'bloko-link bloko-link_kind-tertiary')
        link = table.find('a', class_= 'bloko-link').get('href')
        info1,info2 = None,None
        if guc:
            info1 = guc.find('div', class_= 'bloko-text')
            info2 = guc.find('div', class_= 'bloko-text bloko-text_no-top-indent')

        vacancies.append({
            'Титульник':'',
            'price':'',
            'Описание' :'',
            'Город' :'',
            'Компания':'',
            'Ссылка':''
        })

        if title:
            vacancies[-1].update({'Титульник': title.get_text()})

        if price:
            vacancies[-1].update(pars_prise(price.get_text()))

        if info1 and info2:
            vacancies[-1].update({'Описание': info1.get_text() + info2.get_text()})

        if country:
            vacancies[-1].update({'Город': country.get_text()})

        if company:
            vacancies[-1].update({'Компания': company.get_text()})

        if link:
            vacancies[-1].update({'Ссылка': link})

    return vacancies


def save_exel(info_list):
    with open('data.csv', 'w', errors="ignore") as file:
        writer = csv.writer(file, lineterminator = '\n', delimiter=';')

        charact_keys = ['Титульник','Город','Компания','ЗпОт','ЗпДо','СрЗп','Валюта','Описание','Ссылка']

        writer.writerow(['Index', *charact_keys])
        for index,info in enumerate(info_list):
            charact_values = []
            for key in charact_keys:
                try:
                    charact_values += [info[key]]
                except KeyError:
                    charact_values += [' ']

            writer.writerow([index+1, *charact_values])


def pars_prise(raw_prise):
    global currConv
    prise = [int(s) for s in re.findall(r'-?\d+\.?\d*', raw_prise.replace(' ',''))]
    if len(prise) == 2:
        val = (raw_prise[-4:-1]+raw_prise[-1]).replace('.', '').replace(' ', '').lower()
        prise = [prise[0], prise[1], (prise[0]+prise[1])/2, val]
    else:
        val = (raw_prise[-4:-1]+raw_prise[-1]).replace('.', '').replace(' ', '').lower()
        prise = [prise[0], prise[0], prise[0], val]
    if currConv:
        if prise[3] == 'kzt':
            prise = [prise[0]*0.15, prise[0]*0.15, prise[0]*0.15, 'руб']
        if prise[3] == 'usd':
            prise = [prise[0]*70, prise[0]*70, prise[0]*70, 'руб']
        if prise[3] == 'eur':
            prise = [prise[0]*70, prise[0]*70, prise[0]*70, 'руб']
    return {'ЗпОт':prise[0],'ЗпДо':prise[1],'СрЗп':int(prise[2]),'Валюта':prise[3]}

def get_html(url, params=None):
    html = requests.get(url, params=params, headers=HEADERS)
    return html.text


def main():
    global currConv
    print("Введите ключевое слово:\n")
    kw = input(">>> ")
    print('\n')
    if kw ==  '':
        kw = 'Строитель'
        print(
            "Ключевое стово не распознано\n"
             "Будет использовано ключевое слово поумолчанию\n"
         )
    else:
        print(
            "Ключевое стово распознано\n"
            "Будет использовано введенное ключевое слово\n"
        )

    print("Использовать ли Конвертор валют?(д/н)\n")
    currConv = input(">>> ")
    print('\n')
    if currConv ==  '' or currConv ==  'Н' or currConv ==  'н':
        currConv = False
        print(
             "конвертор валют не будет использован\n"
         )
    else:
        currConv = True
        print(
            "Конвертор валют будет использован\n"
        )            

    print("Сколько собрать страниц?")
    print("\n")
    count_element = input(">>> ")
    print("\n")
    if count_element ==  '':
        count_element = 1
        print(
             "Будет использовано количество страниц по умолчанию\n"
        )
    else:
        count_element = int(count_element)
        print(
            f"Будет проводиться поиск по {count_element} страницам\n"
        )

    info_cards = get_content(URL, kw, count_element)

    print("\nДанне успешно собраны\n")
    save_exel(info_cards)
    print("Данне успешно сохранены\n")
    print(f"\nБыло собрано {len(info_cards)} вакансий \n")


if __name__ == '__main__':
    main()