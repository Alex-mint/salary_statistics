import os
import time
import requests

from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


def get_hh_responses(language):
    url = "https://api.hh.ru/vacancies"
    page_responses = []
    for page in count(0):
        params = {
            "text": f"NAME:Программист {language}",
            "area": 1,
            "page": page,
            "per_page": 100,
            "period": 30,
        }
        page_response = requests.get(url, params)
        page_response.raise_for_status()
        page_response = page_response.json()
        page_responses += page_response["items"]
        if page >= page_response["pages"] - 1:
            break
        time.sleep(0.5)
    found_vacancies = page_response["found"]
    return page_responses, found_vacancies


def get_hh_statistics(languages):
    name = "HeadHunter"
    statistics = {}
    for language in languages:
        responses, found_vacancies = get_hh_responses(language)
        average_salary, processed_vacancies = predict_rub_salary_hh(responses)
        statistics[language] = {"found_vacancies": found_vacancies,
                                "processed_vacancies": processed_vacancies,
                                "average_salary": average_salary,
                                }
    return statistics, name


def predict_rub_salary_hh(response):
    processed_vacancies = 0
    predicted_salary = 0
    for vacancy in response:
        salary = vacancy["salary"]
        if salary and salary["currency"] == "RUR":
            salary_from = salary["from"]
            salary_to = salary["to"]
            calculated_salary = get_predict_salary(salary_from, salary_to)
            processed_vacancies += 1 if calculated_salary else 0
            predicted_salary += calculated_salary
    return get_average_salary(predicted_salary, processed_vacancies)


def get_predict_salary(salary_from, salary_to):
    salary = 0
    if salary_from and salary_to:
        salary = (salary_from + salary_to) / 2
    elif salary_from and not salary_to:
        salary = salary_from * 1.2
    elif not salary_from and salary_to:
        salary = salary_to * 0.8
    elif not salary_from and not salary_to:
        salary = 0
    return salary


def get_sj_responses(language, sj_api_key):
    pages_response = []
    page_number = 0
    page = True
    while page:
        url = "https://api.superjob.ru/2.0/vacancies"
        headers = {
            "X-Api-App-Id": sj_api_key,
        }
        params = {
            "town": "Москва",
            "page": page_number,
            "count": 100,
            "period": 30,
            "keywords": f"Программист {language}"
        }
        page_response = requests.get(url, headers=headers, params=params)
        page_response.raise_for_status()
        page_response = page_response.json()
        page = page_response["more"]
        page_number += 1
        pages_response += page_response["objects"]
    found_vacancies = page_response["total"]
    return pages_response, found_vacancies


def get_sj_statistics(languages, sj_api_key):
    name = "SuperJob"
    statistics = {}
    for language in languages:
        responses, found_vacancies = get_sj_responses(language, sj_api_key)
        average_salary, processed_vacancies = predict_rub_salary_sj(responses)
        statistics[language] = {"found_vacancies": found_vacancies,
                                "processed_vacancies": processed_vacancies,
                                "average_salary": average_salary,
                                }
    return statistics, name


def predict_rub_salary_sj(response):
    processed_vacancies = 0
    predicted_salary = 0
    for vacancy in response:
        if vacancy["currency"] == "rub":
            salary_from = vacancy["payment_from"]
            salary_to = vacancy["payment_to"]
            calculated_salary = get_predict_salary(salary_from, salary_to)
            processed_vacancies += 1 if calculated_salary else 0
            predicted_salary += calculated_salary
    return get_average_salary(predicted_salary, processed_vacancies)


def get_average_salary(predicted_salary, processed_vacancies):
    if processed_vacancies:
        predicted_salary = int(predicted_salary / processed_vacancies)
    else:
        predicted_salary = "Нет данных"
    return predicted_salary, processed_vacancies


def main():
    load_dotenv()
    sj_api_key = os.environ['SUPERJOP_API_KEY']
    languages = ["Python", "Java", "Javascript",
                 "Ruby", "PHP", "C++", "C#", "Go"]
    hh_statistics = get_hh_statistics(languages)
    sj_statistics = get_sj_statistics(languages, sj_api_key)
    all_statistics = [hh_statistics, sj_statistics]
    for statistics, name in all_statistics:
        statistics = [[key, statistics[key]["found_vacancies"],
                       statistics[key]["processed_vacancies"],
                       statistics[key]["average_salary"]] for key in
                      statistics]
        headers = [["Язык программирования", "Вакансий найдено",
                    "Вакансий обработано", "Средняя зарплата"]]
        title = f"{name} Moscow"
        statistics_table = AsciiTable(tuple(headers + statistics), title)
        print(statistics_table.table)


if __name__ == "__main__":
    main()