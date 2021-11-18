from django.shortcuts import render
from django.http import HttpResponse

import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
from io import BytesIO as IO

from .forms import DateForm, UploadFileForm

def index(request):
    if request.method == 'POST':
        date_form = DateForm(request.POST)
        upload_file_form = UploadFileForm(request.POST, request.FILES)
        if date_form.is_valid() and upload_file_form.is_valid():
            cd = date_form.cleaned_data
            business_start_date = cd['date']

            download_excel_file = calculate_employee(request.FILES['file'], business_start_date)

            response = HttpResponse(download_excel_file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', )
            response['Content-Disposition'] = 'attachment; filename=result.xlsx'

            return response
    
    else:
        date_form = DateForm(initial={'date': '2017-01-01'})
        upload_file_form = UploadFileForm()

    return render(request, 'employment_increase_tax_credit/index.html', {'date_form': date_form, 'upload_file_form': upload_file_form})

def last_day_of_month(day):
    next_month = day.replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)

def calculate_age(birthday, today):
    return today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

def calculate_employee(excel_file, business_start_date):
    df = pd.read_excel(excel_file)
        
    df['군복무개월수'] = df['군복무개월수'].fillna(0)
    df['장애인및상이자'] = df['장애인및상이자'].fillna('X')
    df['518민주화운동부상자및고엽제후유의증환자'] = df['518민주화운동부상자및고엽제후유의증환자'].fillna('X')

    end_year = 2021

    start_year = max(2017, business_start_date.year)
    if start_year >= 2017:
        start_month = business_start_date.month
    else:
        start_month = 1

    for index, value in df['생년월일'].items():
        df.loc[index, '입사일나이'] = calculate_age(df.loc[index, '생년월일'], df.loc[index, '입사일자'])

    for year in range(start_year, end_year + 1):
        if year > start_year:
            start_month = 1

        for month in range(start_month, 13):
            date = last_day_of_month(datetime.date(year, month, 1))

            for index, value in df['생년월일'].items():
                if df.loc[index, '군복무개월수'] > 0:
                        # 군복무는 6년을 한도로 연령에서 차감함.
                    value = df.loc[index, '생년월일'] + relativedelta(months = min(df.loc[index, '군복무개월수'], 72))
                df.loc[index, '병역차감나이'] = calculate_age(value, date)
                
            year_month_string = str(year) + '-' + str(month)

            df.loc[(df['입사일자'] <= pd.Timestamp(date)) & ((df['퇴사일자'] >= pd.Timestamp(date)) | df['퇴사일자'].isnull()), year_month_string] = '일반'
                # 29세 이하
            df.loc[(df[year_month_string] == '일반') & (df['병역차감나이'] <= 29), year_month_string] = '청년등'
                # 장애인, 상이자
            df.loc[(df[year_month_string] == '일반') & (df['장애인및상이자'] != 'X'), year_month_string] = '청년등'
                # 518민주화운동부상자, 고엽제후유의증환자 (2019년 1월 1일 이후 개시하는 과세연도 분부터 적용)
            if year >= 2019:
                df.loc[(df[year_month_string] == '일반') & (df['518민주화운동부상자및고엽제후유의증환자'] != 'X'), year_month_string] = '청년등'
                # 근로계약 체결일 현재 연령이 60세 이상인 사람
            if year >= 2021:
                df.loc[(df[year_month_string] == '일반') & (df['입사일나이'] >= 60), year_month_string] = '청년등'
            
    df_summary = pd.DataFrame(index=['청년등근로자수합계', '청년등외근로자수합계', '총상시근로자수합계', '개월수', '청년등근로자수', '청년등외근로자수', '총상시근로자수'], columns=range(start_year, end_year + 1)).fillna(0)

    for index in df:
        if '-' not in index:
            continue

        df.loc['청년등근로자수', index] = df.loc[df[index] == '청년등', index].count()
        df.loc['청년등외근로자수', index] = df.loc[df[index] == '일반', index].count()
        df.loc['총상시근로자수', index] = df.loc['청년등근로자수', index] + df.loc['청년등외근로자수', index]

        df_summary.loc['청년등근로자수합계', int(index[:4])] = df_summary.loc['청년등근로자수합계', int(index[:4])] + df.loc['청년등근로자수', index]
        df_summary.loc['청년등외근로자수합계', int(index[:4])] = df_summary.loc['청년등외근로자수합계', int(index[:4])] + df.loc['청년등외근로자수', index]
        df_summary.loc['총상시근로자수합계', int(index[:4])] = df_summary.loc['총상시근로자수합계', int(index[:4])] + df.loc['총상시근로자수', index]
        df_summary.loc['개월수', int(index[:4])] = df_summary.loc['개월수', int(index[:4])] + 1

    for index in df_summary:
        df_summary.loc['청년등근로자수', index] = int((df_summary.loc['청년등근로자수합계', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['청년등외근로자수', index] = int((df_summary.loc['청년등외근로자수합계', index] / df_summary.loc['개월수', index]) * 100) / 100
        df_summary.loc['총상시근로자수', index] = int((df_summary.loc['총상시근로자수합계', index] / df_summary.loc['개월수', index]) * 100) / 100

    download_excel_file = IO()
    xlwriter = pd.ExcelWriter(download_excel_file, engine='xlsxwriter')
    df.to_excel(xlwriter, '월별근로자수')
    df_summary.to_excel(xlwriter, '근로자수집계')

    xlwriter.save()
    # xlwriter.close()
    download_excel_file.seek(0)

    return download_excel_file